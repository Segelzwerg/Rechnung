from django.shortcuts import render

from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from invoice.models import Address


class AddressCreateView(CreateView):
    model = Address
    fields = '__all__'


class AddressUpdateView(UpdateView):
    model = Address
    fields = '__all__'


class AddressDeleteView(DeleteView):
    model = Address
