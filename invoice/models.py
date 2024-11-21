"""Models for invoice app."""
from math import isnan, isinf

from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db.models import Model, CharField, ForeignKey, CASCADE, EmailField, IntegerField, \
    DateField, UniqueConstraint, FloatField


class Address(Model):
    """Defines any type of address. For vendors as well as customers."""
    street = CharField(max_length=120)
    number = CharField(max_length=120)
    city = CharField(max_length=120)
    country = CharField(max_length=120)


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


class Invoice(Model):
    """Defines an invoice."""
    invoice_number = IntegerField()
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


def validate_real_values(value):
    if isnan(value):
        raise ValidationError('Value must not be nan.')
    if isinf(value):
        raise ValidationError('Value must not be inf or -inf.')


class InvoiceItem(Model):
    """Line item of an invoice."""
    name = CharField(max_length=120)
    description = CharField(max_length=1000)
    quantity = IntegerField(validators=[MinValueValidator(0)])
    price = FloatField(
        validators=[MinValueValidator(-1000000), MaxValueValidator(1000000), validate_real_values])
    tax = FloatField(validators=[MinValueValidator(0.0), MaxValueValidator(1.0)])
    invoice = ForeignKey(Invoice, on_delete=CASCADE)

    @property
    def net_total(self) -> float:
        """Get the sum of the item excluding taxes."""
        return self.price * self.quantity

    @property
    def total(self) -> float:
        """Get the sum of the item including taxes."""
        return self.net_total * (1.0 + self.tax)

    def list_export(self):
        """Get the fields as list."""
        return [self.name, self.description, self.quantity, self.price, self.tax, self.net_total,
                self.total]
