"""Defines the views of the invoice app."""
from django.views.generic import CreateView, UpdateView, DeleteView

from invoice.models import Address, Vendor


class AddressCreateView(CreateView):
    """Create a new address."""
    model = Address
    fields = '__all__'


class AddressUpdateView(UpdateView):
    """Update an existing address."""
    model = Address
    fields = '__all__'


class AddressDeleteView(DeleteView):
    """Delete an existing address."""
    model = Address


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
