"""Defines the views of the invoice app."""
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, ListView, TemplateView

from invoice.forms import InvoiceItemForm
from invoice.models import Address, Vendor, Customer, Invoice, InvoiceItem


class StartView(TemplateView):
    """The start page."""
    template_name = 'invoice/start.html'


class AddressCreateView(CreateView):
    """Create a new address."""
    model = Address
    fields = '__all__'
    success_url = reverse_lazy('address-list')


class AddressUpdateView(UpdateView):
    """Update an existing address."""
    model = Address
    fields = '__all__'
    success_url = reverse_lazy('address-list')


class AddressDeleteView(DeleteView):
    """Delete an existing address."""
    model = Address
    success_url = reverse_lazy('address-list')


class AddressListView(ListView):
    """List all addresses."""
    model = Address


class CustomerCreateView(CreateView):
    """Create a new customer."""
    model = Customer
    fields = '__all__'
    success_url = reverse_lazy('customer-list')


class CustomerUpdateView(UpdateView):
    """Update an existing customer."""
    model = Customer
    fields = '__all__'


class CustomerDeleteView(DeleteView):
    """Delete an existing customer."""
    model = Customer


class CustomerListView(ListView):
    """List all customers."""
    model = Customer


class InvoiceCreateView(CreateView):
    """Create a new invoice."""
    model = Invoice
    fields = '__all__'
    success_url = reverse_lazy('invoice-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invoice_item_form'] = InvoiceItemForm(self.request.POST)
        return context


class InvoiceUpdateView(UpdateView):
    """Update an existing invoice."""
    model = Invoice
    fields = '__all__'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['invoice_item_form'] = InvoiceItemForm(self.request.POST)
        return context


class InvoiceDeleteView(DeleteView):
    """Delete an existing invoice."""
    model = Invoice


class InvoiceListView(ListView):
    """List all invoices."""
    model = Invoice


class InvoiceItemCreateView(CreateView):
    """Create a new invoice item."""
    model = InvoiceItem
    fields = '__all__'
    success_url = reverse_lazy('invoice-list')


class VendorCreateView(CreateView):
    """Create a new vendor."""
    model = Vendor
    fields = '__all__'
    success_url = reverse_lazy('vendor-list')


class VendorUpdateView(UpdateView):
    """Update an existing vendor."""
    model = Vendor


class VendorDeleteView(DeleteView):
    """Delete an existing vendor."""
    model = Vendor


class VendorListView(ListView):
    """List all vendors."""
    model = Vendor
