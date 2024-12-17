"""Defines the views of the invoice app."""
import io

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import FileResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext as _
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.views.generic import TemplateView

from invoice import pdf_generator
from invoice.forms import InvoiceItemForm, AddressForm, BankAccountForm, CustomerForm, VendorForm, InvoiceForm
from invoice.models import Vendor, Customer, Invoice, InvoiceItem


class StartView(TemplateView):
    """The start page."""
    template_name = 'invoice/start.html'


class CustomerCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Create a new customer."""
    template_name = 'invoice/customer_form.html'
    model = Customer
    form_class = CustomerForm
    success_url = reverse_lazy('customer-list')
    success_message = _('Customer was created successfully.')

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
            return self.form_invalid(form)
        address = address_form.save()
        customer = form.save(commit=False)
        customer.address = address
        return super().form_valid(form)


class CustomerUpdateView(SuccessMessageMixin, UpdateView):
    """Update an existing customer."""
    template_name = 'invoice/customer_form.html'
    form_class = CustomerForm
    model = Customer
    success_url = reverse_lazy('customer-list')
    success_message = _('Customer was updated successfully.')

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
            return self.form_invalid(form)
        address_form.save()
        return super().form_valid(form)


class CustomerDeleteView(SuccessMessageMixin, DeleteView):
    """Delete an existing customer."""
    model = Customer
    success_url = reverse_lazy('customer-list')
    success_message = _('Customer was deleted successfully.')


class CustomerListView(ListView):
    """List all customers."""
    model = Customer

    def get_queryset(self, **kwargs):
        """Filter the customer list by the logged-in user."""
        query_set = super().get_queryset(**kwargs)
        return query_set.filter(vendor__user_id=self.request.user.id)


class InvoiceCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Create a new invoice."""
    form_class = InvoiceForm
    model = Invoice
    success_message = _('Invoice was created successfully.')

    def get_success_url(self):
        return reverse('invoice-update', kwargs={'pk': self.object.id})


class InvoiceUpdateView(SuccessMessageMixin, UpdateView):
    """Update an existing invoice."""
    form_class = InvoiceForm
    model = Invoice
    success_url = reverse_lazy('invoice-list')
    success_message = _('Invoice was updated successfully.')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['invoice_item_form'] = InvoiceItemForm(self.request.POST)
        else:
            context['invoice_item_form'] = InvoiceItemForm()
        return context


class InvoicePaidView(SuccessMessageMixin, UpdateView):
    """Mark an invoice as paid"""
    model = Invoice
    fields = ['paid']
    success_message = _('Invoice was marked as paid successfully.')
    template_name = 'invoice/invoice_paid.html'

    def get_success_url(self):
        """Redirect to the invoice detail page."""
        return reverse('invoice-update', kwargs={'pk': self.kwargs['pk']})

    def post(self, request, *args, **kwargs):
        """Mark an invoice as paid."""
        super().post(request, *args, **kwargs)
        self.object.paid = True
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class InvoiceDeleteView(SuccessMessageMixin, DeleteView):
    """Delete an existing invoice."""
    model = Invoice
    success_url = reverse_lazy('invoice-list')
    success_message = _('Invoice was deleted successfully.')


class InvoiceListView(LoginRequiredMixin, ListView):  # pylint: disable=too-many-ancestors
    """List all invoices."""
    model = Invoice

    def get_queryset(self, **kwargs):
        """Filter the invoice list by the logged-in user."""
        query_set = super().get_queryset(**kwargs)
        return query_set.filter(vendor__user_id=self.request.user.id)


@login_required
def pdf_invoice(request, invoice_id) -> HttpResponseForbidden | FileResponse:
    """Generate an invoice as PDF file. It will raise a 403 Forbidden if the user is not the vendor of the invoice."""
    invoice = get_object_or_404(Invoice, pk=invoice_id)
    if invoice.vendor.user != request.user:
        return HttpResponseForbidden("You are not allowed to view this invoice.")
    buffer = io.BytesIO()
    pdf_generator.gen_invoice_pdf(invoice, buffer)
    buffer.seek(0)
    return FileResponse(buffer, as_attachment=False, filename="invoice.pdf")


class InvoiceItemCreateView(SuccessMessageMixin, CreateView):
    """Create a new invoice item."""
    template_name = 'invoice/invoice_form.html'
    form_class = InvoiceItemForm
    model = InvoiceItem
    success_message = _('Invoice item was created successfully.')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoice = get_object_or_404(Invoice, pk=self.kwargs['invoice_id'])
        context['invoice'] = invoice
        context['form'] = InvoiceForm(instance=invoice)
        if self.request.POST:
            context['invoice_item_form'] = InvoiceItemForm(self.request.POST)
        else:
            context['invoice_item_form'] = InvoiceItemForm()
        return context

    def get_success_url(self):
        return reverse('invoice-update', kwargs={'pk': self.kwargs['invoice_id']})

    def form_valid(self, form):
        invoice = get_object_or_404(Invoice, pk=self.kwargs['invoice_id'])
        invoice_item = form.save(commit=False)
        invoice_item.invoice = invoice
        invoice_item.save()
        return super().form_valid(form)


class InvoiceItemUpdateView(SuccessMessageMixin, UpdateView):
    """Update an existing invoice item."""
    template_name = 'invoice/invoice_form.html'
    form_class = InvoiceItemForm
    model = InvoiceItem
    pk_url_kwarg = 'invoice_item_id'
    success_message = _('Invoice item was updated successfully.')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoice_item = self.get_object()
        context['invoice'] = invoice_item.invoice
        context['form'] = InvoiceForm(instance=invoice_item.invoice)
        if self.request.POST:
            context['invoice_item_form'] = InvoiceItemForm(self.request.POST, instance=invoice_item)
        else:
            context['invoice_item_form'] = InvoiceItemForm(instance=invoice_item)
        return context

    def get_success_url(self):
        return reverse('invoice-update', kwargs={'pk': self.kwargs['invoice_id']})


class InvoiceItemDeleteView(SuccessMessageMixin, DeleteView):
    """Delete an existing invoice item."""
    model = InvoiceItem
    pk_url_kwarg = 'invoice_item_id'
    success_message = _('Invoice item was deleted successfully.')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invoice = get_object_or_404(Invoice, pk=self.kwargs['invoice_id'])
        context['invoice'] = invoice
        context['form'] = InvoiceForm(instance=invoice)
        if self.request.POST:
            context['invoice_item_form'] = InvoiceItemForm(self.request.POST)
        else:
            context['invoice_item_form'] = InvoiceItemForm()
        return context

    def get_success_url(self):
        return reverse('invoice-update', kwargs={'pk': self.kwargs['invoice_id']})


class VendorCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    """Create a new vendor. Including a bank account and a new address."""
    template_name = 'invoice/vendor_form.html'
    form_class = VendorForm
    model = Vendor
    success_url = reverse_lazy('vendor-list')
    success_message = _('Vendor was created successfully.')

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
        vendor.user = self.request.user
        return super().form_valid(form)


class VendorUpdateView(SuccessMessageMixin, UpdateView):
    """Update an existing vendor. Including the bank account and address."""
    template_name = 'invoice/vendor_form.html'
    form_class = VendorForm
    model = Vendor
    success_url = reverse_lazy('vendor-list')
    success_message = _('Vendor was updated successfully.')

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
        address_form = AddressForm(self.request.POST, instance=self.object.address)
        if not address_form.is_valid():
            return self.form_invalid(address_form)
        address_form.save()
        bank_account_form = BankAccountForm(self.request.POST, instance=self.object.bank_account)
        if not bank_account_form.is_valid():
            return self.form_invalid(bank_account_form)
        bank_account_form.save()
        return super().form_valid(form)


class VendorDeleteView(SuccessMessageMixin, DeleteView):
    """Delete an existing vendor."""
    model = Vendor
    success_url = reverse_lazy('vendor-list')
    success_message = _('Vendor was deleted successfully.')


class VendorListView(ListView):
    """List all vendors."""
    model = Vendor
