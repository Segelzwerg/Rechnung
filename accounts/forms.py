"""Forms for the authentication app."""

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from django.utils.translation import gettext_lazy as _


class RegistrationForm(UserCreationForm):
    """Form for user registration."""

    email = forms.EmailField(label=_("Email"))
    first_name = forms.CharField(max_length=30, label=_("First name"))
    last_name = forms.CharField(max_length=30, label=_("Last name"))

    # include Meta class
    class Meta:
        model = User
        fields = ["first_name", "last_name", "email", "password1", "password2"]
