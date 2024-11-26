"""Forms of the invoice app"""
from django.forms import ModelForm, Form, CharField

from invoice.models import InvoiceItem


class InvoiceItemForm(ModelForm):
    """Form for invoice items"""

    class Meta:
        model = InvoiceItem
        fields = '__all__'


class CustomerForm(Form):
    """Form for customer including an address."""
    first_name = CharField(max_length=120)
    last_name = CharField(max_length=120)
    email = CharField(max_length=256)
    address_line_1 = CharField(max_length=200)
    address_line_2 = CharField(max_length=200, required=False)
    address_line_3 = CharField(max_length=200, required=False)
    address_postcode = CharField(max_length=10)
    address_city = CharField(max_length=120)
    address_state = CharField(max_length=200, required=False)
    address_country = CharField(max_length=120)
