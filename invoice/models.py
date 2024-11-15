"""Mode
ls for invoice app."""

from django.db.models import Model, CharField, ForeignKey, CASCADE, EmailField, IntegerField, \
    DateField, UniqueConstraint
from django.utils.timezone import now


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
    email = EmailField(max_length=120)
    address = ForeignKey(Address, on_delete=CASCADE)


class Vendor(Model):
    """Defines profiles for the invoicer."""
    name = CharField(max_length=255)
    company_name = CharField(max_length=255, unique=True)
    address: Address = ForeignKey(Address, on_delete=CASCADE)


class Invoice(Model):
    """Defines a invoice."""
    invoice_number = IntegerField()
    date = DateField(default=now())
    vendor = ForeignKey(Vendor, on_delete=CASCADE)
    customer = ForeignKey(Customer, on_delete=CASCADE)

    class Meta:
        """
        Meta configuration of invoice. Ensure uniques of the combination invoice number and
        vendor profile.
        """
        constraints = [UniqueConstraint(fields=['vendor', 'invoice_number'],
                                        name='unique_invoice_numbers_per_vendor')]
