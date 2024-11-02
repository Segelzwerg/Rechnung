from django.db.models import Model
from django.forms import CharField


class Address(Model):
    street = CharField(max_length=120)
    number = CharField(max_length=120)
    city = CharField(max_length=120)
    country = CharField(max_length=120)
