from django.urls import reverse
from hypothesis import given, example
from hypothesis.extra.django import TestCase
from hypothesis.strategies import characters, text

from invoice.models import Address


class AddAddressViewTestCase(TestCase):
    def setUp(self):
        self.url = reverse('address-add')

    @given(text(), text(), text(), text())
    @example("Main Street", "45", "Capital", "Mainland")
    def test_add_address(self, street, number, city, country):
        response = self.client.post(self.url, data={
            'street': street,
            'number': number,
            'city': city,
            'country': country
        }, follow=True)
        address = Address.objects.get(street=street, number=number)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(address)
        self.assertEqual(address.city, city)
        self.assertEqual(address.country, country)
