from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from accounts.forms import RegistrationForm


class RegistrationTest(TestCase):
    """Tests for user registration."""

    def test_registration_form_valid_data(self):
        """Test that the registration form is valid with correct data."""
        form_data = {
            "username": "johndoe",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password1": "securepassword123",
            "password2": "securepassword123",
        }
        form = RegistrationForm(data=form_data)
        self.assertTrue(form.is_valid(), form.errors)

    def test_registration_view_success(self):
        """Test that a user can register via the registration view."""
        url = reverse("signup")
        data = {
            "username": "janesmith",
            "first_name": "Jane",
            "last_name": "Smith",
            "email": "jane@example.com",
            "password1": "anotherpassword456",
            "password2": "anotherpassword456",
        }

        response = self.client.post(url, data)

        self.assertTrue(User.objects.filter(email="jane@example.com").exists())

        user = User.objects.get(email="jane@example.com")
        self.assertEqual(user.first_name, "Jane")
        self.assertEqual(user.last_name, "Smith")

        self.assertEqual(response.status_code, 302)

    def test_registration_passwords_dont_match(self):
        """Test that registration fails if passwords do not match."""
        form_data = {
            "username": "johndoe",
            "first_name": "John",
            "last_name": "Doe",
            "email": "john@example.com",
            "password1": "password123",
            "password2": "mismatch",
        }
        form = RegistrationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors or form.non_field_errors())
