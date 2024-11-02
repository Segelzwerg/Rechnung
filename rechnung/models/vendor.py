from django.db.models import Model, CharField, ForeignKey, CASCADE

from rechnung.models.address import Address


class Vendor(Model):
    name = CharField(max_length=255)
    company_name = CharField(max_length=255, unique=True)
    address: Address = ForeignKey(Address, on_delete=CASCADE)
