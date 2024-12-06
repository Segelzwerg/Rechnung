"""Models for invoice app."""
from decimal import Decimal
from math import isnan, isinf

try:
    from warnings import deprecated
except ImportError:
    from typing_extensions import deprecated

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Model, CharField, ForeignKey, CASCADE, EmailField, IntegerField, \
    DateField, UniqueConstraint, OneToOneField, Q, F, TextChoices
from django.db.models.constraints import CheckConstraint
from django.db.models.fields import DecimalField, BooleanField
from schwifty import IBAN, BIC

from invoice.errors import FinalError

MAX_VALUE_DJANGO_SAVE = 2147483647


class Address(Model):
    """Defines any type of address. For vendors as well as customers."""
    line_1 = CharField(max_length=200)
    line_2 = CharField(max_length=200, null=True, blank=True)
    line_3 = CharField(max_length=200, null=True, blank=True)
    postcode = CharField(max_length=10)
    city = CharField(max_length=120)
    state = CharField(max_length=200, null=True, blank=True)
    country = CharField(max_length=120)

    def __str__(self):
        export = self.line_1
        if self.line_2:
            export += f' {self.line_2}'
        if self.line_3:
            export += f' {self.line_3}'
        export += f', {self.postcode} {self.city}, {self.country}'
        return export


def validate_iban(value):
    """Validate IBAN."""
    try:
        iban = IBAN(value)
        iban.validate()
    except ValueError as err:
        raise ValidationError('Invalid IBAN.') from err


def validate_bic(value):
    """Validate BIC."""
    try:
        BIC(value).validate()
    except ValueError as err:
        raise ValidationError('Invalid BIC.') from err


class BankAccount(Model):
    """Defines a bank account."""
    iban = CharField(max_length=34, validators=[validate_iban])
    bic = CharField(max_length=11, validators=[validate_bic])


class Customer(Model):
    """Defines a customer."""
    first_name = CharField(max_length=120)
    last_name = CharField(max_length=120)
    email = EmailField(max_length=256)
    address = OneToOneField(Address, on_delete=CASCADE)

    @property
    def full_name(self):
        """Get the full name of the customer (first name + last name)."""
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.full_name


class Vendor(Model):
    """Defines profiles for the invoicer."""
    name = CharField(max_length=255)
    company_name = CharField(max_length=255, null=True, blank=True)
    address: Address = OneToOneField(Address, on_delete=CASCADE)
    tax_id = CharField(max_length=120, null=True, blank=True)
    bank_account: BankAccount = OneToOneField(BankAccount, on_delete=CASCADE, null=True, blank=True)

    class Meta:
        """Meta configuration of vendor. Ensures uniques of the combination of name and vendor."""
        constraints = [UniqueConstraint(fields=['name', 'company_name'],
                                        name='unique_name_and_company_name')]

    def __str__(self):
        if self.company_name:
            return self.company_name
        return self.name


class Invoice(Model):
    """Defines an invoice."""

    # pylint: disable=too-many-ancestors
    class Currency(TextChoices):
        """Definition of commonly used currencies."""
        EUR = 'EUR', 'Euro'
        USD = 'USD', 'US Dollar'
        JPY = 'JPY', 'Japanese Yen'
        GBP = 'GBP', 'Pound Sterling'
        CHF = 'CHF', 'Swiss Franc'
        CAD = 'CAD', 'Canadian Dollar'
        AUD = 'AUD', 'Australian Dollar'
        NZD = 'NZD', 'New Zealand Dollar'
        SEK = 'SEK', 'Swedish Krona'
        DKK = 'DKK', 'Danish Krone'
        NOK = 'NOK', 'Norwegian Krone'
        HKD = 'HKD', 'Hong Kong Dollar'
        CNY = 'CNY', 'Chinese Yuan'

    invoice_number = IntegerField(validators=[MaxValueValidator(MAX_VALUE_DJANGO_SAVE)])
    date = DateField()
    vendor = ForeignKey(Vendor, on_delete=CASCADE)
    customer = ForeignKey(Customer, on_delete=CASCADE)
    currency = CharField(max_length=3, choices=Currency, default=Currency.EUR)
    due_date = DateField(null=True, blank=True)
    final = BooleanField(default=False)

    class Meta:
        """
        Meta configuration of invoice. Ensure uniques of the combination invoice number and
        vendor profile.
        """
        constraints = [UniqueConstraint(fields=['vendor', 'invoice_number'],
                                        name='unique_invoice_numbers_per_vendor'),
                       CheckConstraint(check=Q(due_date__gte=F('date')), name='due_date_gte_date')]

    def save(self, *args, **kwargs):
        """Save invoice unless it is marked final. Then an FinalError is raised."""
        if self.final and self.pk is not None:
            initial = Invoice.objects.get(pk=self.pk)
            if initial.final:
                raise FinalError()
        super().save(*args, **kwargs)

    @property
    def items(self):
        """Get list of invoice items."""
        return list(self.invoiceitem_set.all())

    @property
    def table_export(self):
        """Get the line items as list and export all of them as table with a header row."""
        header = ['Name', 'Description', 'Quantity', 'Price', 'Tax', 'Net Total', 'Total']
        item_list = [item.list_export for item in self.items]
        return [header] + item_list

    @property
    def net_total(self) -> Decimal:
        """Get the sum of net total."""
        return Decimal(sum(item.net_total for item in self.items))

    @property
    def total(self) -> Decimal:
        """Get the sum of total."""
        return Decimal(sum(item.total for item in self.items))

    @property
    def net_total_string(self) -> str:
        """Get the net total string."""
        return f'{self.net_total:.2f} {self.currency}'

    @property
    def total_string(self) -> str:
        """Get the total string."""
        return f'{self.total:.2f} {self.currency}'


@deprecated('Deprecated in 0.1 and remove in 1.0')
def validate_real_values(value):
    """Validate real values."""
    if isnan(value):
        raise ValidationError('Value must not be nan.')
    if isinf(value):
        raise ValidationError('Value must not be inf or -inf.')


@deprecated('Deprecated in 0.1 and remove in 1.0')
def validate_two_digits_decimals(value):
    """Allow only two decimal digits."""
    if str(value)[::-1].find('.') > 2:
        raise ValidationError('Price must have only two decimal digits.')


class InvoiceItem(Model):
    """Line item of an invoice."""
    name = CharField(max_length=120)
    description = CharField(max_length=1000)
    quantity = DecimalField(max_digits=19, decimal_places=4,
                            validators=[MinValueValidator(Decimal('0.0000')),
                                        MaxValueValidator(Decimal('1000000.0000'))])
    unit = CharField(max_length=120, null=True, blank=True)
    price = DecimalField(max_digits=19, decimal_places=2,
                         validators=[MinValueValidator(Decimal('-1000000.00')),
                                     MaxValueValidator(Decimal('1000000.00'))])
    tax = DecimalField(max_digits=5, decimal_places=4,
                       validators=[MinValueValidator(Decimal('0.0000')),
                                   MaxValueValidator(Decimal('1.0000'))])
    invoice = ForeignKey(Invoice, on_delete=CASCADE)

    @property
    def net_total(self) -> Decimal:
        """Get the sum of the item excluding taxes."""
        return self.price * self.quantity

    @property
    def total(self) -> Decimal:
        """Get the sum of the item including taxes."""
        return self.net_total * (Decimal('1.0') + self.tax)

    @property
    def list_export(self):
        """Get the fields as list with formatted fields of totals."""
        return [self.name,
                self.description,
                self.quantity_string,
                self.price_string,
                self.tax_string,
                self.net_total_string,
                self.total_string]

    @property
    def net_total_string(self) -> str:
        """Get the net total string."""
        return f'{self.net_total:.2f} {self.invoice.currency}'

    @property
    def price_string(self) -> str:
        """Get the price string."""
        return f'{self.price:.2f} {self.invoice.currency}'

    @property
    def quantity_string(self) -> str:
        """Get the quantity string."""
        quantity = f'{self.quantity:.4f}'.rstrip('0').rstrip('.,')
        return f'{quantity} {self.unit}'

    @property
    def tax_string(self) -> str:
        """Get the tax string."""
        s = f'{self.tax * 100:.2f}'.rstrip('0').rstrip('.,')
        return f'{s}%'

    @property
    def total_string(self) -> str:
        """Get the total string."""
        return f'{self.total:.2f} {self.invoice.currency}'
