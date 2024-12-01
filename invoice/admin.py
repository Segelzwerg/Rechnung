"""Admin registration for invoice app."""
from django.contrib import admin

from invoice.models import Vendor, Address, Customer, BankAccount, Invoice, InvoiceItem


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Enable to manage address from admin panel."""


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    """Enable to manage bank account from admin panel."""


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    """Enable to manage vendor from admin panel."""


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Enable to manage customer from admin panel."""


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Enable to manage invoice from admin panel."""


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    """Enable to manage invoice item from admin panel."""
