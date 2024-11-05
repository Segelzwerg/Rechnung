from django.urls import path

from invoice.views import AddressCreateView, AddressUpdateView, AddressDeleteView, VendorCreateView, \
    VendorUpdateView, VendorDeleteView

urlpatterns = [
    # ...
    path("address/add/", AddressCreateView.as_view(), name="address-add"),
    path("address/<int:pk>/", AddressUpdateView.as_view(), name="address-update"),
    path("address/<int:pk>/delete/", AddressDeleteView.as_view(), name="address-delete"),
    path("vendor/add/", VendorCreateView.as_view(), name="vendor-add"),
    path("vendor/<int:pk>/", VendorUpdateView.as_view(), name="vendor-update"),
    path("vendor/<int:pk>/delete/", VendorDeleteView.as_view(), name="vendor-delete"),
]
