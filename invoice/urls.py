"""Defines the URLs for the invoice app."""

from django.urls import path

from invoice import views

urlpatterns = [
    path("", views.StartView.as_view(), name="start"),
    path("customers/", views.CustomerListView.as_view(), name="customer-list"),
    path("customer/add/", views.CustomerCreateView.as_view(), name="customer-add"),
    path("customer/<int:pk>/", views.CustomerUpdateView.as_view(), name="customer-update"),
    path("customer/<int:pk>/delete/", views.CustomerDeleteView.as_view(), name="customer-delete"),
    path("invoices/", views.InvoiceListView.as_view(), name="invoice-list"),
    path("invoice/add/", views.InvoiceCreateView.as_view(), name="invoice-add"),
    path("invoice/<int:pk>/", views.InvoiceUpdateView.as_view(), name="invoice-update"),
    path("invoice/<int:invoice_id>/pdf/", views.pdf_invoice, name="invoice-pdf"),
    path("invoice/<int:pk>/delete/", views.InvoiceDeleteView.as_view(), name="invoice-delete"),
    path("invoice/<int:pk>/paid/", views.InvoicePaidView.as_view(), name="invoice-paid"),
    path("invoice/<int:invoice_id>/item/", views.InvoiceItemCreateView.as_view(), name="invoice-item-add"),
    path(
        "invoice/<int:invoice_id>/item/<int:invoice_item_id>/",
        views.InvoiceItemUpdateView.as_view(),
        name="invoice-item-update",
    ),
    path(
        "invoice/<int:invoice_id>/item/<int:invoice_item_id>/delete/",
        views.InvoiceItemDeleteView.as_view(),
        name="invoice-item-delete",
    ),
    path("vendors/", views.VendorListView.as_view(), name="vendor-list"),
    path("vendor/add/", views.VendorCreateView.as_view(), name="vendor-add"),
    path("vendor/<int:pk>/", views.VendorUpdateView.as_view(), name="vendor-update"),
    path("vendor/<int:pk>/delete/", views.VendorDeleteView.as_view(), name="vendor-delete"),
    path(
        "invoice/generate-number/",
        views.InvoiceGenerateNumberView.as_view(),
        name="invoice-generate-number",
    ),

]
