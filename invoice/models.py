"""Models for invoice app."""
from decimal import Decimal
from math import isnan, isinf
from warnings import deprecated

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Model, CharField, ForeignKey, CASCADE, EmailField, IntegerField, \
    DateField, UniqueConstraint
from django.db.models.fields import DecimalField
from schwifty import IBAN, BIC

MAX_VALUE_DJANGO_SAVE = 2147483647


class Address(Model):
    """Defines any type of address. For vendors as well as customers."""
    street = CharField(max_length=200)
    postcode = CharField(max_length=10)
    city = CharField(max_length=120)
    country = CharField(max_length=120)


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
    iban = CharField(max_length=34, validators=[validate_iban], unique=True)
    bic = CharField(max_length=11, validators=[validate_bic])


class Customer(Model):
    """Defines a customer."""
    first_name = CharField(max_length=120)
    last_name = CharField(max_length=120)
    email = EmailField(max_length=256)
    address = ForeignKey(Address, on_delete=CASCADE)


class Vendor(Model):
    """Defines profiles for the invoicer."""
    name = CharField(max_length=255)
    company_name = CharField(max_length=255, unique=True)
    address: Address = ForeignKey(Address, on_delete=CASCADE)
    tax_id = CharField(max_length=120, null=True, blank=True)
    bank_account: BankAccount = ForeignKey(BankAccount, on_delete=CASCADE, null=True, blank=True)


class Invoice(Model):
    """Defines an invoice."""
    invoice_number = IntegerField(validators=[MaxValueValidator(MAX_VALUE_DJANGO_SAVE)])
    date = DateField()
    vendor = ForeignKey(Vendor, on_delete=CASCADE)
    customer = ForeignKey(Customer, on_delete=CASCADE)

    class Meta:
        """
        Meta configuration of invoice. Ensure uniques of the combination invoice number and
        vendor profile.
        """
        constraints = [UniqueConstraint(fields=['vendor', 'invoice_number'],
                                        name='unique_invoice_numbers_per_vendor')]

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
    def total(self):
        """Get the sum of total."""
        return sum(item.total for item in self.items)


@deprecated('Deprecated in 0.1 and remove in 1.0')
def validate_real_values(value):
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
    quantity = IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(MAX_VALUE_DJANGO_SAVE)])
    price = DecimalField(max_digits=19, decimal_places=2,
                         validators=[MinValueValidator(-1000000),
                                     MaxValueValidator(1000000)])
    tax = DecimalField(max_digits=3, decimal_places=2,
                       validators=[MinValueValidator(0.00),
                                   MaxValueValidator(1.00)])
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
        """Get the fields as list."""
        return [self.name, self.description, self.quantity, self.price, self.tax_string,
                self.net_total,
                self.total]

    @property
    def tax_string(self) -> str:
        return f'{self.tax * 100}%'
