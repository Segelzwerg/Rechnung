"""Admin registration for invoice app."""
from django.contrib import admin

from invoice.models import Vendor, Address


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Enable to manage address from admin panel."""


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    """Enable to manage vendor from admin panel."""
