"""Defines the views of the invoice app."""
import io
from warnings import catch_warnings

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import FileResponse, HttpResponseRedirect, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils.http import urlencode
from django.utils.translation import gettext as _
from django.views.generic import CreateView, UpdateView, DeleteView, ListView
from django.views.generic import TemplateView

from invoice import pdf_generator
from invoice.errors import IncompliantWarning
from invoice.forms import InvoiceItemForm, AddressForm, BankAccountForm, CustomerForm, VendorForm, InvoiceForm
from invoice.models import Vendor, Customer, Invoice, InvoiceItem


class OwnMixin(UserPassesTestMixin):
    """Use in views that have an object with a vendor field to verify ownership."""

    def test_func(self):
        """Check if the user is the owner of the object via a vendor field."""
        return self.request.user == self.get_object().vendor.user

    def handle_no_permission(self, login_redirect='start', permission_redirect='start'):
        """
        Redirects to login if the user is not authenticated. Otherwise, redirect to the the permission page.
        :param login_redirect: Name of the target view after logging in as an owner.
        :param permission_redirect: Name of the target view if user's permissions are not sufficient.
        :return: HTTP redirect.
        """
        if self.request.user.is_authenticated:
            messages.warning(self.request, self.permission_denied_message)
            return HttpResponseRedirect(reverse(permission_redirect))
        next_url = reverse(login_redirect, args=[self.kwargs['pk']])
        base_url = reverse('login')
        url = '{}?{}'.format(base_url, urlencode({'next': next_url}))  # pylint: disable=consider-using-f-string
        return HttpResponseRedirect(url)


class OwnVendorMixin(UserPassesTestMixin):
    """Use in views that have a vendor object to verify ownership."""

    def test_func(self):
        """Check if the user is the owner of the object via vendor's user."""
        return self.request.user == self.get_object().user

    def handle_no_permission(self, login_redirect='start', permission_redirect='start'):
        """
        Redirects to login if the user is not authenticated. Otherwise, redirect to the the permission page.
        :param login_redirect: Name of the target view after logging in as an owner.
        :param permission_redirect: Name of the target view if user's permissions are not sufficient.
        :return: HTTP redirect.
        """
        if self.request.user.is_authenticated:
            messages.warning(self.request, self.permission_denied_message)
            return HttpResponseRedirect(reverse(permission_redirect))
        next_url = reverse(login_redirect, args=[self.kwargs['pk']])
        base_url = reverse('login')
        url = '{}?{}'.format(base_url, urlencode({'next': next_url}))  # pylint: disable=consider-using-f-string
        return HttpResponseRedirect(url)


class OwnItemMixin(UserPassesTestMixin):
    """Use in views that are invoice item related and require a permission check."""

    def test_func(self):
        """Check if the user is the owner of the customer."""
        invoice_id = self.kwargs['invoice_id']
        invoice = get_object_or_404(Invoice, pk=invoice_id)
        return self.request.user == invoice.vendor.user

    def handle_no_permission(self, login_args=None, permission_redirect='start', login_redirect='start'):
        """
        Redirects to login if the user is not authenticated. Otherwise, redirect to the the permission page.
        :param login_args: Arguments to login redirect.
        :param login_redirect: Name of the target view after logging in as an owner.
        :param permission_redirect: Name of the target view if user's permissions are not sufficient.
        :return: HTTP redirect.
        """
        if self.request.user.is_authenticated:
            messages.warning(self.request, self.permission_denied_message)
            return HttpResponseRedirect(reverse(permission_redirect))
        next_url = reverse(login_redirect, args=login_args)
        base_url = reverse('login')
        url = '{}?{}'.format(base_url, urlencode({'next': next_url}))  # pylint: disable=consider-using-f-string
        return HttpResponseRedirect(url)


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
        context['form'].fields['vendor'].queryset = Vendor.objects.filter(user_id=self.request.user.id)
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


class CustomerUpdateView(OwnMixin, SuccessMessageMixin, UpdateView):
    """Update an existing customer."""
    template_name = 'invoice/customer_form.html'
    form_class = CustomerForm
    model = Customer
    success_url = reverse_lazy('customer-list')
    success_message = _('Customer was updated successfully.')
    permission_denied_message = _('You are not allowed to edit this customer.')

    def handle_no_permission(self, login_redirect='customer-update', permission_redirect='customer-list'):
        return super().handle_no_permission(login_redirect, permission_redirect)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'].fields['vendor'].queryset = Vendor.objects.filter(user_id=self.request.user.id)
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


class CustomerDeleteView(OwnMixin, SuccessMessageMixin, DeleteView):
    """Delete an existing customer."""
    model = Customer
    success_url = reverse_lazy('customer-list')
    success_message = _('Customer was deleted successfully.')

    def handle_no_permission(self, login_redirect='customer-delete', permission_redirect='customer-list'):
        return super().handle_no_permission(login_redirect, permission_redirect)


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


class InvoiceUpdateView(OwnMixin, SuccessMessageMixin, UpdateView):
    """Update an existing invoice."""
    form_class = InvoiceForm
    model = Invoice
    success_url = reverse_lazy('invoice-list')
    success_message = _('Invoice was updated successfully.')

    def form_valid(self, form):
        """Raises a warning message if set final and is not compliant."""
        with catch_warnings(record=True) as warning:
            super().form_valid(form)
            if len([_ for _ in warning if issubclass(_.category, IncompliantWarning)]) > 0:
                messages.warning(self.request, "The invoice is not compliant.")
                next_url = reverse('invoice-update', args=[self.kwargs['pk']])
                return HttpResponseRedirect(next_url)
        return HttpResponseRedirect(self.get_success_url())

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['invoice_item_form'] = InvoiceItemForm(self.request.POST)
        else:
            context['invoice_item_form'] = InvoiceItemForm()
        return context

    def handle_no_permission(self, login_redirect='invoice-update', permission_redirect='invoice-list'):
        return super().handle_no_permission(login_redirect, permission_redirect)


class InvoicePaidView(OwnMixin, SuccessMessageMixin, UpdateView):
    """Mark an invoice as paid"""
    model = Invoice
    fields = ['paid']
    success_message = _('Invoice was marked as paid successfully.')
    template_name = 'invoice/invoice_paid.html'

    def handle_no_permission(self, login_redirect='invoice-paid', permission_redirect='invoice-list'):
        return super().handle_no_permission(login_redirect, permission_redirect)

    def get_success_url(self):
        """Redirect to the invoice detail page."""
        return reverse('invoice-update', kwargs={'pk': self.kwargs['pk']})

    def post(self, request, *args, **kwargs):
        """Mark an invoice as paid."""
        super().post(request, *args, **kwargs)
        self.object.paid = True
        self.object.save()
        return HttpResponseRedirect(self.get_success_url())


class InvoiceDeleteView(OwnMixin, SuccessMessageMixin, DeleteView):
    """Delete an existing invoice."""
    model = Invoice
    success_url = reverse_lazy('invoice-list')
    success_message = _('Invoice was deleted successfully.')

    def handle_no_permission(self, login_redirect='invoice-delete', permission_redirect='invoice-list'):
        return super().handle_no_permission(login_redirect, permission_redirect)


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


class InvoiceItemCreateView(OwnItemMixin, SuccessMessageMixin, CreateView):
    """Create a new invoice item."""
    template_name = 'invoice/invoice_form.html'
    form_class = InvoiceItemForm
    model = InvoiceItem
    success_message = _('Invoice item was created successfully.')

    def handle_no_permission(self, login_args=None, permission_redirect='invoice-list',
                             login_redirect='invoice-item-add'):
        if login_args is None:
            login_args = [self.kwargs['invoice_id']]
        return super().handle_no_permission(login_redirect=login_redirect, login_args=login_args,
                                            permission_redirect=permission_redirect, )

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


class InvoiceItemUpdateView(OwnItemMixin, SuccessMessageMixin, UpdateView):
    """Update an existing invoice item."""
    template_name = 'invoice/invoice_form.html'
    form_class = InvoiceItemForm
    model = InvoiceItem
    pk_url_kwarg = 'invoice_item_id'
    success_message = _('Invoice item was updated successfully.')

    def handle_no_permission(self, login_args=None, permission_redirect='invoice-list',
                             login_redirect='invoice-item-update'):
        if login_args is None:
            login_args = [self.kwargs['invoice_id'], self.kwargs['invoice_item_id']]
        return super().handle_no_permission(login_redirect=login_redirect, login_args=login_args,
                                            permission_redirect=permission_redirect, )

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


class InvoiceItemDeleteView(OwnItemMixin, SuccessMessageMixin, DeleteView):
    """Delete an existing invoice item."""
    model = InvoiceItem
    pk_url_kwarg = 'invoice_item_id'
    success_message = _('Invoice item was deleted successfully.')

    def handle_no_permission(self, login_args=None, permission_redirect='invoice-list',
                             login_redirect='invoice-item-delete'):
        if login_args is None:
            login_args = [self.kwargs['invoice_id'], self.kwargs['invoice_item_id']]
        return super().handle_no_permission(login_redirect=login_redirect, login_args=login_args,
                                            permission_redirect=permission_redirect, )

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


class VendorUpdateView(OwnVendorMixin, SuccessMessageMixin, UpdateView):
    """Update an existing vendor. Including the bank account and address."""
    template_name = 'invoice/vendor_form.html'
    form_class = VendorForm
    model = Vendor
    success_url = reverse_lazy('vendor-list')
    success_message = _('Vendor was updated successfully.')

    def handle_no_permission(self, login_redirect='vendor-update', permission_redirect='vendor-list'):
        return super().handle_no_permission(login_redirect=login_redirect, permission_redirect=permission_redirect)

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


class VendorDeleteView(OwnVendorMixin, SuccessMessageMixin, DeleteView):
    """Delete an existing vendor."""
    model = Vendor
    success_url = reverse_lazy('vendor-list')
    success_message = _('Vendor was deleted successfully.')

    def handle_no_permission(self, login_redirect='vendor-delete', permission_redirect='vendor-list'):
        return super().handle_no_permission(login_redirect=login_redirect, permission_redirect=permission_redirect)


class VendorListView(ListView):
    """List all vendors."""
    model = Vendor

    def get_queryset(self, **kwargs):
        """Filter the customer list by the logged-in user."""
        query_set = super().get_queryset(**kwargs)
        return query_set.filter(user_id=self.request.user.id)
