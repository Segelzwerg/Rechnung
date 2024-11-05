"""Defines the URLs for the invoice app."""
from django.urls import path

from invoice import views

urlpatterns = [
    # ...
    path("address/add/", views.AddressCreateView.as_view(), name="address-add"),
    path("address/<int:pk>/", views.AddressUpdateView.as_view(), name="address-update"),
    path("address/<int:pk>/delete/", views.AddressDeleteView.as_view(), name="address-delete"),
    path("vendor/add/", views.VendorCreateView.as_view(), name="vendor-add"),
    path("vendor/<int:pk>/", views.VendorUpdateView.as_view(), name="vendor-update"),
    path("vendor/<int:pk>/delete/", views.VendorDeleteView.as_view(), name="vendor-delete"),
]
