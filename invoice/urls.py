"""Defines the URLs for the invoice app."""
from django.urls import path

from invoice import views

urlpatterns = [
    # ...
    path("address/add/", views.AddressCreateView.as_view(), name="address-add"),
    path("address/<int:pk>/", views.AddressUpdateView.as_view(), name="address-update"),
    path("address/<int:pk>/delete/", views.AddressDeleteView.as_view(), name="address-delete"),
    path("addresses/", views.AddressListView.as_view(), name="address-list"),
    path("customer/add/", views.CustomerCreateView.as_view(), name="customer-add"),
    path("customer/<int:pk>/", views.CustomerUpdateView.as_view(), name="customer-update"),
    path("customer/<int:pk>/delete/", views.CustomerDeleteView.as_view(), name="customer-delete"),
    path("customers/", views.CustomerListView.as_view(), name="customer-list"),
    path("invoice/add/", views.InvoiceCreateView.as_view(), name="invoice-add"),
    path("invoice/<int:pk>/", views.InvoiceUpdateView.as_view(), name="invoice-update"),
    path("invoice/<int:pk>/delete/", views.InvoiceDeleteView.as_view(), name="invoice-delete"),
    path("invoices/", views.InvoiceListView.as_view(), name="invoice-list"),
    path("vendor/add/", views.VendorCreateView.as_view(), name="vendor-add"),
    path("vendor/<int:pk>/", views.VendorUpdateView.as_view(), name="vendor-update"),
    path("vendor/<int:pk>/delete/", views.VendorDeleteView.as_view(), name="vendor-delete"),
    path("vendors/", views.VendorListView.as_view(), name="vendor-list"),

]
