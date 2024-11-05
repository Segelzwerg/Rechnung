from django.urls import path

from invoice.views import AddressCreateView, AddressUpdateView, AddressDeleteView

urlpatterns = [
    # ...
    path("address/add/", AddressCreateView.as_view(), name="address-add"),
    path("address/<int:pk>/", AddressUpdateView.as_view(), name="address-update"),
    path("address/<int:pk>/delete/", AddressDeleteView.as_view(), name="address-delete"),
]
