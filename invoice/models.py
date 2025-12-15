"""Models for invoice app."""

import operator
import warnings
from collections import Counter
from decimal import Decimal
from functools import reduce
from math import isinf, isnan
from warnings import deprecated

# This is the recommended way as per django documentation.
# Source: https://docs.djangoproject.com/en/5.1/topics/auth/customizing/#extending-the-existing-user-model
# pylint: disable=imported-auth-user
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models import (
    CASCADE,
    BooleanField,
    CharField,
    DateField,
    EmailField,
    F,
    ForeignKey,
    IntegerField,
    Model,
    OneToOneField,
    Q,
    TextChoices,
    UniqueConstraint,
)
from django.db.models.constraints import CheckConstraint
from django.db.models.fields import DecimalField
from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.utils.translation import gettext_lazy as _
from django.utils.translation import pgettext_lazy
from schwifty import BIC, IBAN

from invoice.errors import FinalError, IncompliantWarning

MAX_VALUE_DJANGO_SAVE = 2147483647


class Address(Model):
    """Defines any type of address. For vendors as well as customers."""

    line_1 = CharField(_("first address line"), max_length=200)
    line_2 = CharField(_("second address line"), max_length=200, blank=True, default="")
    line_3 = CharField(_("third address line"), max_length=200, blank=True, default="")
    postcode = CharField(_("postcode"), max_length=10)
    city = CharField(_("city"), max_length=120)
    state = CharField(_("state"), max_length=200, blank=True, default="")
    country = CharField(_("country"), max_length=120)

    class Meta:
        verbose_name = _("address")
        verbose_name_plural = _("addresses")

    def __str__(self):
        export = self.line_1
        if self.line_2:
            export += f" {self.line_2}"
        if self.line_3:
            export += f" {self.line_3}"
        export += f", {self.postcode} {self.city}, {self.country}"
        return export


def validate_iban(value):
    """Validate IBAN."""
    try:
        iban = IBAN(value)
        iban.validate()
    except ValueError as err:
        raise ValidationError(_("Invalid IBAN.")) from err


def validate_bic(value):
    """Validate BIC."""
    try:
        BIC(value).validate()
    except ValueError as err:
        raise ValidationError(_("Invalid BIC.")) from err


class BankAccount(Model):
    """Defines a bank account."""

    owner = CharField(pgettext_lazy("account owner", "owner"), max_length=120, default="")
    iban = CharField(_("IBAN"), max_length=120, validators=[validate_iban])
    bic = CharField(_("BIC"), max_length=120, validators=[validate_bic])

    class Meta:
        verbose_name = _("bank account")
        verbose_name_plural = _("bank accounts")

    def __str__(self):
        return f"BankAccount({self.owner},{self.iban},{self.bic})"

    def save(self, *args, **kwargs):
        """Save the bank account."""
        self.iban = IBAN(self.iban)
        if self.iban.bic:
            # Overwrites the BIC regardless of the user input.
            self.bic = self.iban.bic
        elif self.bic:
            self.bic = BIC(self.bic)
        super().save(*args, **kwargs)


class Customer(Model):
    """Defines a customer."""

    first_name = CharField(_("first name"), max_length=120)
    last_name = CharField(_("last name"), max_length=120)
    email = EmailField(_("email"), max_length=256)
    address = OneToOneField(Address, verbose_name=_("address"), on_delete=CASCADE)
    vendor = ForeignKey("Vendor", verbose_name=_("vendor"), on_delete=CASCADE)
    invoice_counter = IntegerField(_("invoice counter"), default=0)

    class Meta:
        verbose_name = _("customer")
        verbose_name_plural = _("customers")

    def __str__(self):
        return self.full_name

    @property
    def full_name(self):
        """Get the full name of the customer (first name + last name)."""
        return f"{self.first_name} {self.last_name}"

    def get_next_invoice_counter(self) -> int:
        """Get the next invoice number based on the counter and saves the new number as current counter."""
        self.invoice_counter += 1
        self.save()
        return self.invoice_counter


@receiver(post_delete, sender=Customer)
def post_delete_customer(sender, instance, *args, **kwargs):  # pylint: disable=unused-argument # noqa: ARG001
    """Delete customer one-to-one fields when customer is deleted."""
    try:
        x = instance.address
        if x:
            x.delete()
    except (KeyError, ObjectDoesNotExist):
        pass


class Vendor(Model):
    """Defines profiles for the invoicer."""

    name = CharField(_("name"), max_length=255)
    company_name = CharField(_("company name"), max_length=255, blank=True, default="")
    address: Address = OneToOneField(Address, verbose_name=_("address"), on_delete=CASCADE)
    tax_id = CharField(_("tax ID"), max_length=120, blank=True, default="")
    bank_account: BankAccount = OneToOneField(
        BankAccount, verbose_name=_("bank account"), on_delete=CASCADE, null=True, blank=True
    )
    user = ForeignKey(User, on_delete=CASCADE)
    invoice_counter = IntegerField(_("invoice counter"), default=0)

    class Meta:
        """Meta configuration of vendor. Ensures uniques of the combination of name and vendor."""

        verbose_name = _("vendor")
        verbose_name_plural = _("vendors")
        constraints = [UniqueConstraint(fields=["name", "company_name"], name="unique_name_and_company_name")]

    def __str__(self):
        if self.company_name:
            return self.company_name
        return self.name

    def get_next_invoice_counter(self) -> int:
        """Get the next invoice number based on the counter and saves the new number as current counter."""
        self.invoice_counter += 1
        self.save()
        return self.invoice_counter


@receiver(post_delete, sender=Vendor)
def post_delete_vendor(sender, instance, *args, **kwargs):  # pylint: disable=unused-argument # noqa: ARG001
    """Delete vendor one-to-one fields when vendor is deleted."""
    try:
        x = instance.address
        if x:
            x.delete()
    except (KeyError, ObjectDoesNotExist):
        pass
    try:
        x = instance.bank_account
        if x:
            x.delete()
    except (KeyError, ObjectDoesNotExist):
        pass


class Invoice(Model):
    """Defines an invoice."""

    # pylint: disable=too-many-ancestors
    class Currency(TextChoices):
        """Definition of commonly used currencies."""

        EUR = "EUR", _("Euro")
        USD = "USD", _("US Dollar")
        JPY = "JPY", _("Japanese Yen")
        GBP = "GBP", _("Pound Sterling")
        CHF = "CHF", _("Swiss Franc")
        CAD = "CAD", _("Canadian Dollar")
        AUD = "AUD", _("Australian Dollar")
        NZD = "NZD", _("New Zealand Dollar")
        SEK = "SEK", _("Swedish Krona")
        DKK = "DKK", _("Danish Krone")
        NOK = "NOK", _("Norwegian Krone")
        HKD = "HKD", _("Hong Kong Dollar")
        CNY = "CNY", _("Chinese Yuan")

    invoice_number = IntegerField(
        _("invoice number"), validators=[MaxValueValidator(MAX_VALUE_DJANGO_SAVE)], null=True, blank=True
    )
    date = DateField(_("date"))
    vendor = ForeignKey(Vendor, verbose_name=_("vendor"), on_delete=CASCADE)
    customer = ForeignKey(Customer, verbose_name=_("customer"), on_delete=CASCADE)
    currency = CharField(_("currency"), max_length=3, choices=Currency, default=Currency.EUR)
    due_date = DateField(_("due date"), null=True, blank=True)
    delivery_date = DateField(_("delivery date"), null=True, blank=True)
    paid = BooleanField(_("paid"), default=False)
    final = BooleanField(_("final"), default=False)

    class Meta:
        """
        Meta configuration of invoice.

        Ensures uniques of the combination invoice number and
        vendor profile.
        """

        verbose_name = _("invoice")
        verbose_name_plural = _("invoices")
        constraints = [
            UniqueConstraint(fields=["vendor", "invoice_number"], name="unique_invoice_numbers_per_vendor"),
            CheckConstraint(condition=Q(due_date__gte=F("date")), name="due_date_gte_date"),
        ]

    def __str__(self):
        return f"Invoice({self.invoice_number},{self.vendor},{self.customer})"

    def save(self, *args, **kwargs):
        """Save invoice unless it is marked final. Then a FinalError is raised."""
        if self.final and self.pk is not None:
            initial = Invoice.objects.get(pk=self.pk)
            if initial.final:
                raise FinalError

        if self.final and not self.compliant:
            warnings.warn("Invoice is not compliant", IncompliantWarning, stacklevel=2)
        super().save(*args, **kwargs)

    @property
    def items(self) -> list[InvoiceItem]:
        """Get list of invoice items. Returns empty list if the invoice is not saved yet."""
        if self.pk is None:
            return []
        return list(self.invoiceitem_set.all())

    @property
    def table_export(self):
        """Get the line items as list and export all of them as table with a header row."""
        header = [_("Name"), _("Description"), _("Quantity"), _("Price"), _("Tax"), _("Net Total"), _("Total")]
        item_list = [item.list_export for item in self.items]
        return [header, *item_list]

    @property
    def net_total(self) -> Decimal:
        """Get the sum of net total."""
        return Decimal(sum(item.net_total for item in self.items))

    @property
    def tax_amount(self) -> Decimal:
        """Get the sum of tax amount."""
        return Decimal(sum(item.tax_amount for item in self.items))

    @property
    def tax_amount_per_rate(self) -> dict[str, Decimal]:
        """Get the sum of tax amount per tax rate."""
        if self.items:
            tax_rates = [{item.tax_string: item.tax_amount} for item in self.items]
            return dict(reduce(operator.add, map(Counter, tax_rates)))
        return {}

    @property
    def total(self) -> Decimal:
        """Get the sum of total."""
        return self.net_total + self.tax_amount

    @property
    def net_total_rounded(self) -> Decimal:
        """Get the sum of net total rounded to two decimals."""
        return self.net_total.quantize(Decimal("0.01"))

    @property
    def tax_amount_rounded(self) -> Decimal:
        """Get the sum of tax amount rounded to two decimals."""
        return self.tax_amount.quantize(Decimal("0.01"))

    @property
    def total_rounded(self) -> Decimal:
        """Get the sum of total rounded to two decimals."""
        return self.net_total_rounded + self.tax_amount_rounded

    @property
    def net_total_string(self) -> str:
        """Get the net total string."""
        return f"{self.net_total_rounded} {self.currency}"

    @property
    def tax_amount_strings(self) -> dict[str, str]:
        """Get the tax amount strings as dictionary with the rate as key and the amount string as value."""
        return {
            rate: f"{amount.quantize(Decimal('0.01'))} {self.currency}"
            for rate, amount in self.tax_amount_per_rate.items()
        }

    @property
    def total_string(self) -> str:
        """Get the total string."""
        return f"{self.total_rounded} {self.currency}"

    @property
    def compliant(self) -> bool:
        """Get if the invoice is compliant."""
        if not self.items:
            return False
        if not self.delivery_date:
            return False
        if not self.vendor.tax_id:  # noqa: SIM103
            return False
        return True


@deprecated("Deprecated in 0.1 and remove in 1.0")
def validate_real_values(value):
    """Validate real values."""
    if isnan(value):
        raise ValidationError("Value must not be nan.")
    if isinf(value):
        raise ValidationError("Value must not be inf or -inf.")


@deprecated("Deprecated in 0.1 and remove in 1.0")
def validate_two_digits_decimals(value):
    """Allow only two decimal digits."""
    if str(value)[::-1].find(".") > 2:  # noqa: PLR2004
        raise ValidationError("Price must have only two decimal digits.")


class InvoiceItem(Model):
    """Line item of an invoice."""

    name = CharField(_("invoice item"), max_length=120)
    description = CharField(_("description"), max_length=1000)
    quantity = DecimalField(
        _("quantity"),
        max_digits=19,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0000")), MaxValueValidator(Decimal("1000000.0000"))],
    )
    unit = CharField(_("unit"), max_length=120, blank=True, default="")
    price = DecimalField(
        _("price"),
        max_digits=19,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("-1000000.00")), MaxValueValidator(Decimal("1000000.00"))],
    )
    tax = DecimalField(
        _("tax rate"),
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0000")), MaxValueValidator(Decimal("1.0000"))],
    )
    invoice = ForeignKey(Invoice, verbose_name=_("invoice"), on_delete=CASCADE)

    def __str__(self):
        return f"InvoiceItem({self.quantity}x{self.name},{self.price})"

    @property
    def net_total(self) -> Decimal:
        """Get the sum of the item excluding taxes."""
        return self.price * self.quantity

    @property
    def tax_amount(self) -> Decimal:
        """Get the monetary amount of tax."""
        return self.net_total * self.tax

    @property
    def total(self) -> Decimal:
        """Get the sum of the item including taxes."""
        return self.net_total + self.tax_amount

    @property
    def net_total_rounded(self) -> Decimal:
        """Get the net total rounded to two decimals."""
        return self.net_total.quantize(Decimal("0.01"))

    @property
    def tax_amount_rounded(self) -> Decimal:
        """Get the tax amount rounded to two decimals."""
        return self.tax_amount.quantize(Decimal("0.01"))

    @property
    def total_rounded(self) -> Decimal:
        """Get the total rounded to two decimals."""
        return self.net_total_rounded + self.tax_amount_rounded

    @property
    def list_export(self):
        """Get the fields as list with formatted fields of totals."""
        return [
            self.name,
            self.description,
            self.quantity_string,
            self.price_string,
            self.tax_string,
            self.net_total_string,
            self.total_string,
        ]

    @property
    def price_string(self) -> str:
        """Get the price string."""
        return f"{self.price:.2f} {self.invoice.currency}"

    @property
    def quantity_string(self) -> str:
        """Get the quantity string including the unit."""
        quantity = f"{self.quantity:.4f}".rstrip("0").rstrip(".,")
        if self.unit:
            return f"{quantity} {self.unit}"
        return quantity

    @property
    def tax_string(self) -> str:
        """Get the tax rate string."""
        s = f"{self.tax * 100:.2f}".rstrip("0").rstrip(".,")
        return f"{s}%"

    @property
    def net_total_string(self) -> str:
        """Get the net total string."""
        return f"{self.net_total_rounded} {self.invoice.currency}"

    @property
    def tax_amount_string(self) -> str:
        """Get the tax amount string."""
        return f"{self.tax_amount_rounded} {self.invoice.currency}"

    @property
    def total_string(self) -> str:
        """Get the total string."""
        return f"{self.total_rounded} {self.invoice.currency}"
