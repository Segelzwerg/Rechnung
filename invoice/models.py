"""Models for invoice app."""
from django.db.models import Model, CharField, ForeignKey, CASCADE


class Address(Model):
    """Defines any type of address. For vendors as well as customers."""
    street = CharField(max_length=120)
    number = CharField(max_length=120)
    city = CharField(max_length=120)
    country = CharField(max_length=120)


class Vendor(Model):
    """Defines profiles for the invoicer."""
    name = CharField(max_length=255)
    company_name = CharField(max_length=255, unique=True)
    address: Address = ForeignKey(Address, on_delete=CASCADE)
