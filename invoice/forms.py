"""Forms of the invoice app"""
from django.forms import ModelForm, Form, CharField

from invoice.models import InvoiceItem, Customer, Address


class InvoiceItemForm(ModelForm):
    """Form for invoice items"""

    class Meta:
        model = InvoiceItem
        fields = '__all__'


class CustomerForm(ModelForm):
    """Form for customer."""

    class Meta:
        model = Customer
        fields = '__all__'


class AddressForm(ModelForm):
    """Form for address."""

    class Meta:
        model = Address
        fields = '__all__'


class VendorForm(Form):
    """Form for vendor including an address."""
    name = CharField(max_length=255)
    company_name = CharField(max_length=255)
    tax_id = CharField(max_length=120, required=False)
    bank_iban = CharField(max_length=34, required=False)
    bank_bic = CharField(max_length=11, required=False)
    address_line_1 = CharField(max_length=200)
    address_line_2 = CharField(max_length=200, required=False)
    address_line_3 = CharField(max_length=200, required=False)
    address_postcode = CharField(max_length=10)
    address_city = CharField(max_length=120)
    address_state = CharField(max_length=200, required=False)
    address_country = CharField(max_length=120)
