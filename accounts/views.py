"""Views for the accounts app."""

from django.urls import reverse_lazy
from django.views.generic import CreateView

from accounts.forms import RegistrationForm


class SignUpView(CreateView):
    """Create a new user in the system."""

    form_class = RegistrationForm
    success_url = reverse_lazy("login")
    template_name = "registration/signup.html"
