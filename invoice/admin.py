"""Admin registration for invoice app."""

from django.contrib import admin

from invoice.models import Address, BankAccount, Customer, Invoice, InvoiceItem, Vendor


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Enable to manage address from admin panel."""

    def get_queryset(self, request):
        """Filter addresses by vendor."""
        return Address.objects.filter(vendor__user=request.user)


@admin.register(BankAccount)
class BankAccountAdmin(admin.ModelAdmin):
    """Enable to manage bank account from admin panel."""

    def get_queryset(self, request):
        """Filter bank accounts by vendor."""
        return BankAccount.objects.filter(vendor__user=request.user)


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    """Enable to manage vendor from admin panel."""

    def get_queryset(self, request):
        """Filter vendors by user."""
        return Vendor.objects.filter(user=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Restrict vendor selection to user."""
        kwargs["queryset"] = Vendor.objects.filter(user=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    """Enable to manage customer from admin panel."""

    def get_queryset(self, request):
        """Filter customers by vendor."""
        return Customer.objects.filter(vendor__user=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Restrict customer selection to vendor."""
        kwargs["queryset"] = Vendor.objects.filter(user=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    """Enable to manage invoice from admin panel."""

    def get_queryset(self, request):
        """Filter invoices by customer."""
        return Invoice.objects.filter(customer__vendor__user=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Restrict invoice selection to vendor."""
        kwargs["queryset"] = Vendor.objects.filter(user=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(InvoiceItem)
class InvoiceItemAdmin(admin.ModelAdmin):
    """Enable to manage invoice item from admin panel."""

    def get_queryset(self, request):
        """Filter invoice items by invoice."""
        return InvoiceItem.objects.filter(invoice__customer__vendor__user=request.user)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Restrict invoice item selection to vendor."""
        kwargs["queryset"] = Vendor.objects.filter(user=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
