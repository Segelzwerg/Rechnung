"""Defines the views of the invoice app."""
import io

from django.http import FileResponse
from django.urls import reverse_lazy
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.views.generic import TemplateView
from reportlab.pdfgen import canvas
from reportlab.platypus import Table

from invoice.forms import InvoiceItemForm, AddressForm, BankAccountForm, CustomerForm, VendorForm
from invoice.models import Vendor, Customer, Invoice, InvoiceItem

A4_WIDTH = 595


class StartView(TemplateView):
    """The start page."""
    template_name = 'invoice/start.html'


class CustomerCreateView(CreateView):
    """Create a new customer."""
    template_name = 'invoice/customer_form.html'
    model = Customer
    form_class = CustomerForm
    success_url = reverse_lazy('customer-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['address_form'] = AddressForm(self.request.POST)
        else:
            context['address_form'] = AddressForm()
        return context

    def form_valid(self, form):
        """Create a new customer and a new address."""
        address_form = AddressForm(self.request.POST)
        if not address_form.is_valid():
            return self.form_invalid(address_form)
        address = address_form.save()
        customer = form.save(commit=False)
        customer.address = address
        return super().form_valid(form)


class CustomerUpdateView(UpdateView):
    """Update an existing customer."""
    template_name = 'invoice/customer_form.html'
    form_class = CustomerForm
    model = Customer
    success_url = reverse_lazy('customer-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['address_form'] = AddressForm(self.request.POST)
        else:
            context['address_form'] = AddressForm(instance=self.object.address)
        return context

    def form_valid(self, form):
        """Updates an existing customer including the address."""
        address_form = AddressForm(instance=self.object.address, data=self.request.POST)
        if not address_form.is_valid():
            return self.form_invalid(address_form)
        address_form.save()
        return super().form_valid(form)


class CustomerDeleteView(DeleteView):
    """Delete an existing customer."""
    model = Customer
    success_url = reverse_lazy('customer-list')


class CustomerListView(ListView):
    """List all customers."""
    model = Customer


class InvoiceCreateView(CreateView):
    """Create a new invoice."""
    model = Invoice
    fields = '__all__'

    def get_success_url(self):
        return reverse_lazy('invoice-update', kwargs={'pk': self.object.id})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['invoice_item_form'] = InvoiceItemForm(self.request.POST)
        else:
            context['invoice_item_form'] = InvoiceItemForm()
        return context


class InvoiceUpdateView(UpdateView):
    """Update an existing invoice."""
    model = Invoice
    fields = '__all__'
    success_url = reverse_lazy('invoice-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['invoice_item_form'] = InvoiceItemForm(self.request.POST)
        else:
            context['invoice_item_form'] = InvoiceItemForm()
        return context


class InvoiceDeleteView(DeleteView):
    """Delete an existing invoice."""
    model = Invoice
    success_url = reverse_lazy('invoice-list')


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
    if invoice.vendor.company_name:
        pdf_object.drawString(100, 780, invoice.vendor.company_name)
    pdf_object.drawString(100, 760, invoice.vendor.address.line_1)
    if invoice.vendor.address.line_2:
        pdf_object.drawString(100, 740, invoice.vendor.address.line_2)
    if invoice.vendor.address.line_3:
        pdf_object.drawString(100, 720, invoice.vendor.address.line_3)
    pdf_object.drawString(100, 700,
                          f'{invoice.vendor.address.postcode} {invoice.vendor.address.city}')
    pdf_object.drawString(100, 680, invoice.vendor.address.country)
    pdf_object.drawString(100, 640, 'Rechnung')
    data = Invoice.objects.get(id=invoice_id).table_export
    table = Table(data=data)
    _, table_height = table.wrapOn(pdf_object, 0, 0)
    table.drawOn(pdf_object, x=100, y=table_y_start)
    pdf_object.drawString(A4_WIDTH - 250, table_y_start - table_height,
                          f'Net Total: {invoice.net_total:.2f}')
    pdf_object.drawString(A4_WIDTH - 250, table_y_start - table_height - 20,
                          f'Total: {invoice.total:.2f}')
    if invoice.vendor.tax_id:
        pdf_object.drawString(100, 100, f'Tax ID: {invoice.vendor.tax_id}')
    if invoice.vendor.bank_account:
        pdf_object.drawString(100, 80, f'IBAN: {invoice.vendor.bank_account.iban}')
        pdf_object.drawString(100, 60, f'BIC: {invoice.vendor.bank_account.bic}')
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
    """Create a new vendor. Including a bank account and a new address."""
    template_name = 'invoice/vendor_form.html'
    form_class = VendorForm
    model = Vendor
    success_url = reverse_lazy('vendor-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['address_form'] = AddressForm(self.request.POST)
            context['bank_form'] = BankAccountForm(self.request.POST)
        else:
            context['address_form'] = AddressForm()
            context['bank_form'] = BankAccountForm()
        return context

    def form_valid(self, form):
        """Create a new vendor, a new address and a new bank account."""
        address_form = AddressForm(self.request.POST)
        if not address_form.is_valid():
            return self.form_invalid(address_form)
        address = address_form.save()
        bank_account_form = BankAccountForm(self.request.POST)
        if not bank_account_form.is_valid():
            return self.form_invalid(bank_account_form)
        bank_account = bank_account_form.save()
        vendor = form.save(commit=False)
        vendor.address = address
        vendor.bank_account = bank_account
        return super().form_valid(form)


class VendorUpdateView(UpdateView):
    """Update an existing vendor. Including the bank account and address."""
    template_name = 'invoice/vendor_form.html'
    form_class = VendorForm
    model = Vendor
    success_url = reverse_lazy('vendor-list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['address_form'] = AddressForm(self.request.POST)
            context['bank_form'] = BankAccountForm(self.request.POST)
        else:
            context['address_form'] = AddressForm(instance=self.object.address)
            context['bank_form'] = BankAccountForm(instance=self.object.bank_account)
        return context

    def form_valid(self, form):
        """Updates an existing vendor including the address and the bank account."""
        address_form = AddressForm(instance=self.object.address, data=self.request.POST)
        if not address_form.is_valid():
            return self.form_invalid(address_form)
        address_form.save()
        bank_account_form = BankAccountForm(instance=self.object.bank_account,
                                            data=self.request.POST)
        if not bank_account_form.is_valid():
            return self.form_invalid(bank_account_form)
        bank_account_form.save()
        return super().form_valid(form)


class VendorDeleteView(DeleteView):
    """Delete an existing vendor."""
    model = Vendor
    success_url = reverse_lazy('vendor-list')


class VendorListView(ListView):
    """List all vendors."""
    model = Vendor
