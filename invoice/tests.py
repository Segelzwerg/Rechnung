from django.urls import reverse
from hypothesis import given, example
from hypothesis.extra.django import TestCase
from hypothesis.strategies import characters, text, emails

from invoice.models import Address, Customer


class AddAddressViewTestCase(TestCase):
    def setUp(self):
        self.url = reverse('address-add')

    @given(text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd']), min_size=1),
           text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd']), min_size=1),
           text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd']), min_size=1),
           text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd']), min_size=1))
    @example("Main Street", "45", "Capital", "Mainland")
    @example(street='0', number='0', city='0', country='\r', ).xfail(reason='"\r" is not a '
                                                                            'valid input.')
    def test_add_address(self, street, number, city, country):
        response = self.client.post(self.url, data={
            'street': street,
            'number': number,
            'city': city,
            'country': country
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/addresses/')
        address = Address.objects.get(street=street, number=number)

        self.assertIsNotNone(address)
        self.assertEqual(address.city, city)
        self.assertEqual(address.country, country)


class AddCustomerViewTestCase(TestCase):
    def setUp(self):
        self.url = reverse('customer-add')

    @given(text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd']), min_size=1),
           text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd']), min_size=1),
           emails())
    @example("John", "Doe", "john@doe.com")
    def test_add_customer(self, first_name, last_name, email):
        address = Address.objects.create(street="Main Street", number="45", city="Capital",
                                         country="Mainland")
        response = self.client.post(self.url, data={
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'address': 1
        }, follow=True)
        customer = Customer.objects.get(first_name=first_name, last_name=last_name)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(customer)
        self.assertEqual(customer.email, email)
        self.assertEqual(customer.address, address)
