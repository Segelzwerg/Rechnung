"""Defines the views of the invoice app."""
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView

from invoice.models import Address, Vendor, Customer, Invoice


class AddressCreateView(CreateView):
    """Create a new address."""
    model = Address
    fields = '__all__'
    success_url = reverse_lazy('address-list')


class AddressUpdateView(UpdateView):
    """Update an existing address."""
    model = Address
    fields = '__all__'


class AddressDeleteView(DeleteView):
    """Delete an existing address."""
    model = Address


class CustomerCreateView(CreateView):
    """Create a new customer."""
    model = Customer
    fields = '__all__'


class CustomerUpdateView(UpdateView):
    """Update an existing customer."""
    model = Customer
    fields = '__all__'


class CustomerDeleteView(DeleteView):
    """Delete an existing customer."""
    model = Customer


class InvoiceCreateView(CreateView):
    """Create a new invoice."""
    model = Invoice
    fields = '__all__'


class InvoiceUpdateView(UpdateView):
    """Update an existing invoice."""
    model = Invoice
    fields = '__all__'


class InvoiceDeleteView(DeleteView):
    """Delete an existing invoice."""
    model = Invoice


class VendorCreateView(CreateView):
    """Create a new vendor."""
    model = Vendor
    fields = '__all__'


class VendorUpdateView(UpdateView):
    """Update an existing vendor."""
    model = Vendor


class VendorDeleteView(DeleteView):
    """Delete an existing vendor."""
    model = Vendor
