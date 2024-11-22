"""Defines the views of the invoice app."""
import io

from django.http import FileResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.views.generic import TemplateView
from reportlab.pdfgen import canvas
from reportlab.platypus import Table

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


def pdf_invoice(request, invoice_id) -> FileResponse:
    """Generate an invoice as PDF file."""
    buffer = io.BytesIO()
    pdf_object = canvas.Canvas(buffer)
    invoice = Invoice.objects.get(id=invoice_id)
    table_y_start = 600
    pdf_object.drawString(100, 800, invoice.vendor.name)
    pdf_object.drawString(100, 780, invoice.vendor.company_name)
    pdf_object.drawString(100, 760, invoice.vendor.address.street + " " +
                          invoice.vendor.address.number)
    pdf_object.drawString(100, 740, invoice.vendor.address.city)
    pdf_object.drawString(100, 720, invoice.vendor.address.country)
    pdf_object.drawString(100, 660, 'Rechnung')
    data = Invoice.objects.get(id=invoice_id).table_export
    table = Table(data=data)
    table_width, table_height = table.wrapOn(pdf_object, 0, 0)
    table.drawOn(pdf_object, x=100, y=table_y_start)
    pdf_object.drawString(350, table_y_start - table_height, f'Net Total: {invoice.net_total}')
    pdf_object.drawString(350, table_y_start - table_height - 20, f'Total: {invoice.total}')
    pdf_object.showPage()
    pdf_object.save()
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=False, filename='invoice.pdf')


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
