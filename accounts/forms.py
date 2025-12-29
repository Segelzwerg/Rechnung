"""Forms for the authentication app."""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User  # pylint: disable=imported-auth-user
from django.utils.translation import gettext_lazy as _


class RegistrationForm(UserCreationForm):  # pylint: disable=too-many-ancestors
    """Form for user registration."""

    email = forms.EmailField(label=_("Email"))
    first_name = forms.CharField(max_length=30, label=_("First name"))
    last_name = forms.CharField(max_length=30, label=_("Last name"))

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "password1", "password2"]
