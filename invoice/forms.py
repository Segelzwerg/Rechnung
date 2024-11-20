"""Forms of the invoice app"""
from django.forms import ModelForm

from invoice.models import InvoiceItem


class InvoiceItemForm(ModelForm):
    """Form for invoice items"""

    class Meta:
        model = InvoiceItem
        fields = '__all__'
