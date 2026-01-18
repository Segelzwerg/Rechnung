"""Forms of the invoice app."""
from django.forms import ModelForm
from django.forms.widgets import DateInput

from invoice.models import Address, BankAccount, Customer, Invoice, InvoiceItem, Vendor


class InvoiceForm(ModelForm):
    """Form for invoices."""

    class Meta:
        model = Invoice
        fields = ["date", "due_date", "delivery_date", "vendor", "customer", "currency", "paid", "final"]
        widgets = {
            "date": DateInput(attrs={"type": "date-local"}),
            "due_date": DateInput(attrs={"type": "date-local"}),
            "delivery_date": DateInput(attrs={"type": "date-local"}),
        }

    def __init__(self, *args, **kwargs):
        """Initialize the form."""
        user = kwargs.pop("user", None)  # Get the user passed from the view
        super().__init__(*args, **kwargs)
        if user:
            # Filter the vendors and customers by the current user
            self.fields["vendor"].queryset = Vendor.objects.filter(user=user)
            self.fields["customer"].queryset = Customer.objects.filter(vendor__user=user)


class InvoiceItemForm(ModelForm):
    """Form for invoice items."""

    class Meta:
        model = InvoiceItem
        fields = ["name", "description", "quantity", "unit", "price", "tax"]


class CustomerForm(ModelForm):
    """Form for customer."""

    class Meta:
        model = Customer
        fields = ["first_name", "last_name", "email", "vendor"]

    def __init__(self, *args, **kwargs):
        """Initialize the form."""
        user = kwargs.pop("user", None)  # Get the user passed from the view
        super().__init__(*args, **kwargs)
        if user:
            # Filter the vendors and customers by the current user
            self.fields["vendor"].queryset = Vendor.objects.filter(user=user)


class AddressForm(ModelForm):
    """Form for address."""

    class Meta:
        model = Address
        fields = ["line_1", "line_2", "line_3", "postcode", "city", "state", "country"]

class BankAccountForm(ModelForm):
    """Form for bank account."""

    class Meta:
        model = BankAccount
        fields = ["owner", "iban", "bic"]


class VendorForm(ModelForm):
    """Form for vendor including an address."""

    class Meta:
        model = Vendor
        fields = ["name", "company_name", "tax_id"]
