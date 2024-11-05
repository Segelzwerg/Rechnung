from django.views.generic import CreateView, UpdateView, DeleteView

from invoice.models import Address, Vendor


class AddressCreateView(CreateView):
    model = Address
    fields = '__all__'


class AddressUpdateView(UpdateView):
    model = Address
    fields = '__all__'


class AddressDeleteView(DeleteView):
    model = Address


class VendorCreateView(CreateView):
    model = Vendor
    fields = '__all__'


class VendorUpdateView(UpdateView):
    model = Vendor


class VendorDeleteView(DeleteView):
    model = Vendor
