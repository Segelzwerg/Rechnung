"""Forms of the invoice app"""
from django.forms import ModelForm
from django.forms.widgets import DateInput

from invoice.models import InvoiceItem, Customer, Address, BankAccount, Vendor, Invoice


class InvoiceForm(ModelForm):
    """Form for invoices"""

    class Meta:
        model = Invoice
        fields = ['invoice_number', 'date', 'vendor', 'customer', 'currency']
        widgets = {
            'date': DateInput(attrs={'type': 'date'}),
        }


class InvoiceItemForm(ModelForm):
    """Form for invoice items"""

    class Meta:
        model = InvoiceItem
        fields = ['name', 'description', 'quantity', 'price', 'tax']


class CustomerForm(ModelForm):
    """Form for customer."""

    class Meta:
        model = Customer
        fields = ['first_name', 'last_name', 'email']


class AddressForm(ModelForm):
    """Form for address."""

    class Meta:
        model = Address
        fields = '__all__'


class BankAccountForm(ModelForm):
    """Form for bank account."""

    class Meta:
        model = BankAccount
        fields = '__all__'


class VendorForm(ModelForm):
    """Form for vendor including an address."""

    class Meta:
        model = Vendor
        fields = ['name', 'company_name', 'tax_id']
