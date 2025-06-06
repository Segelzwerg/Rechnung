from datetime import timedelta
from decimal import Decimal
from math import inf, nan

import schwifty
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.timezone import now
from hypothesis import given, example, assume
from hypothesis.extra.django import TestCase
from hypothesis.provisional import domains
from hypothesis.strategies import characters, text, emails, composite, decimals, \
    sampled_from, lists

from invoice.errors import FinalError
from invoice.models import Address, Customer, Vendor, InvoiceItem, Invoice, MAX_VALUE_DJANGO_SAVE, \
    BankAccount

GERMAN_TAX_RATE = Decimal('0.19')
HUNDRED = Decimal('100')
ONE = Decimal('1')


@composite
def build_customer_fields(draw):
    first_name = draw(text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd', 'Zs', 'Pd']),
                           min_size=1))
    last_name = draw(text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd', 'Zs', 'Pd']),
                          min_size=1))
    email = draw(emails(domains=domains(max_length=255, max_element_length=63)))

    assume(first_name.strip() == first_name)
    assume(last_name.strip() == last_name)
    assume(email.strip() == email)
    return first_name, last_name, email


@composite
def build_vendor_fields(draw):
    name = draw(text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd', 'Zs', 'Pd']), min_size=1))
    company_name = draw(text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd', 'Zs', 'Pd']), min_size=1))
    tax_id = draw(text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd', 'Zs', 'Pd'])))

    assume(name.strip() == name)
    assume(company_name.strip() == company_name)
    assume(tax_id.strip() == tax_id)
    return name, company_name, tax_id


@composite
def build_address_fields(draw):
    address_line_1 = draw(text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd', 'Zs', 'Pd']),
                               min_size=1))
    address_line_2 = draw(text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd', 'Zs', 'Pd'])))
    address_line_3 = draw(text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd', 'Zs', 'Pd'])))
    city = draw(text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd', 'Zs', 'Pd']),
                     min_size=1))
    postcode = draw(text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd', 'Zs', 'Pd']),
                         min_size=1, max_size=10))
    state = draw(text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd', 'Zs', 'Pd'])))
    country = draw(text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd', 'Zs', 'Pd']),
                        min_size=1))

    assume(address_line_1.strip() == address_line_1)
    assume(address_line_2.strip() == address_line_2)
    assume(address_line_3.strip() == address_line_3)
    assume(city.strip() == city)
    assume(postcode.strip() == postcode)
    assume(state.strip() == state)
    assume(country.strip() == country)
    return address_line_1, address_line_2, address_line_3, city, postcode, state, country


@composite
def build_bank_fields(draw):
    country_code = draw(sampled_from(['DE', 'AT', 'CH', 'GB', 'LU', 'NL', 'PL', 'SE', 'LT', 'PL']))
    owner = draw(text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd', 'Zs', 'Pd']),
                      min_size=1))
    iban = schwifty.IBAN.random(country_code=country_code)
    bic = iban.bic

    assume(owner.strip() == owner)
    assume(bic)
    return owner, iban, bic


@composite
def build_invoice_item(draw):
    name = draw(text(min_size=1))
    description = draw(text(min_size=1))
    quantity = draw(decimals(places=4, min_value=0, max_value=1000000, allow_infinity=False, allow_nan=False))
    unit = draw(text())
    price = draw(decimals(max_value=1000000, min_value=-1000000, places=2, allow_infinity=False, allow_nan=False))
    tax = draw(decimals(places=4, min_value=0, max_value=1, allow_infinity=False, allow_nan=False))

    assume(name.strip() == name)
    assume(description.strip() == description)
    assume(unit.strip() == unit)
    return InvoiceItem(name=name, description=description, quantity=quantity, unit=unit, price=price, tax=tax)


class AddCustomerViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username="test", password="password")

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()

    def setUp(self):
        self.url = reverse('customer-add')

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoice/customer_form.html')

    @given(build_customer_fields(), build_address_fields())
    @example(('John', 'Doe', 'john@doe.com'),
             ('Musterstraße 1', '', '', 'Musterstadt', '12345', '', 'Germany'))
    def test_add_customer(self, customer_fields, address_fields):
        self.client.force_login(self.user)
        first_name, last_name, email = customer_fields
        address_line_1, address_line_2, address_line_3, city, postcode, state, country = address_fields
        vendor_address = Address.objects.create(line_1=address_line_1 + 'a', line_2=address_line_2,
                                                line_3=address_line_3,
                                                city=city, postcode=postcode, state=state, country=country)
        vendor = Vendor.objects.create(name="Test", company_name="Test", user=self.user, address=vendor_address)
        response = self.client.post(self.url, data={
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'line_1': address_line_1,
            'line_2': address_line_2,
            'line_3': address_line_3,
            'city': city,
            'postcode': postcode,
            'state': state,
            'country': country,
            'vendor': vendor.id,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/customers/')
        customer = Customer.objects.get(first_name=first_name, last_name=last_name)
        address = Address.objects.get(line_1=address_line_1)
        self.assertIsNotNone(customer)
        self.assertIsNotNone(address)
        self.assertEqual(customer.email, email)
        self.assertEqual(customer.address, address)

    def test_update_invalid_input_address(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data={
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@doe.com',
            'line_1': '',
            'city': 'Musterstadt',
            'postcode': '12345',
            'country': 'Germany',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context_data['address_form'], 'line_1',
                             errors=['This field is required.'])

    def test_login_required(self):
        url = reverse("customer-add")
        response = self.client.post(f"{url}", follow=True)
        self.assertRedirects(response, f"/accounts/login/?next={url}")


class UpdateCustomerViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username="test", password="password")
        address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        cls.vendor = Vendor.objects.create(name="Test", company_name="Test", user=cls.user, address=address)

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()
        Vendor.objects.all().delete()

    def setUp(self):
        self.customer = Customer.objects.create(first_name="John", last_name="Doe", email="John@doe.com",
                                                address=Address.objects.create(
                                                    line_1='Musterstraße 1',
                                                    postcode='12345', city='Musterstadt',
                                                    country='Germany'),
                                                vendor=self.vendor)
        self.url = reverse('customer-update', args=[self.customer.id])

    def tearDown(self):
        Customer.objects.all().delete()

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoice/customer_form.html')

    @given(build_customer_fields(), build_address_fields())
    def test_update_vendor(self, customer_fields, address_fields):
        self.client.force_login(self.user)
        first_name, last_name, email = customer_fields
        address_line_1, address_line_2, address_line_3, city, postcode, state, country = address_fields
        response = self.client.post(self.url, data={
            'first_name': first_name,
            'last_name': last_name,
            'email': email,
            'line_1': address_line_1,
            'line_2': address_line_2,
            'line_3': address_line_3,
            'city': city,
            'postcode': postcode,
            'state': state,
            'country': country,
            'vendor': self.vendor.id,
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/customers/')
        customer = Customer.objects.get(first_name=first_name, last_name=last_name)
        address = Address.objects.get(line_1=address_line_1)
        self.assertIsNotNone(customer)
        self.assertEqual(customer.email, email)
        self.assertEqual(customer.address, address)

    def test_update_invalid_input_customer(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data={
            'first_name': 'John',
            'last_name': '',
            'email': 'john@doe.com',
            'line_1': 'Musterstraße 1',
            'city': 'Musterstadt',
            'postcode': '12345',
            'country': 'Germany',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context_data['form'], 'last_name',
                             errors=['This field is required.'])

    def test_update_invalid_input_address(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data={
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@doe.com',
            'line_1': '',
            'city': 'Musterstadt',
            'postcode': '12345',
            'country': 'Germany',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context_data['address_form'], 'line_1',
                             errors=['This field is required.'])

    def test_auth_required(self):
        url = reverse("customer-update", args=[self.customer.id])
        response = self.client.post(f"{url}", follow=True)
        self.assertRedirects(response, f"/accounts/login/?next={url}")

    def test_not_own_customer_get(self):
        self.client.force_login(self.user)
        second_user = User.objects.create_user(username="test2", password="<PASSWORD>")
        address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor_address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor = Vendor.objects.create(name="Test22", company_name="Test22", user=second_user, address=vendor_address)
        customer = Customer.objects.create(first_name="John", last_name="Doe", email="John@doe.com", address=address,
                                           vendor=vendor)
        url = reverse('customer-update', args=[customer.id])
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/customers/')

    def test_not_own_customer_post(self):
        self.client.force_login(self.user)
        second_user = User.objects.create_user(username="test2", password="<PASSWORD>")

        address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor_address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor = Vendor.objects.create(name="Test22", company_name="Test22", user=second_user, address=vendor_address)
        customer = Customer.objects.create(first_name="John", last_name="Doe", email="John@doe.com", address=address,
                                           vendor=vendor)
        url = reverse('customer-update', args=[customer.id])
        first_name = 'John'
        response = self.client.post(url, data={
            'first_name': first_name,
        }, follow=True)
        self.assertRedirects(response, '/customers/')


class CustomerListViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username="test", password="password")
        address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        cls.vendor = Vendor.objects.create(name="Test", company_name="Test", user=cls.user, address=address)
        cls.url = reverse('customer-list')

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()

    def test_only_users_customers(self):
        second_user = User.objects.create_user(username="test2", password="<PASSWORD>")
        second_address = Address.objects.create(line_1="Test2", postcode="12345", city="Test2", country="Germany")
        second_vendor = Vendor.objects.create(name="Test2", company_name="Test2", user=second_user,
                                              address=second_address)
        customer = Customer.objects.create(first_name="John", last_name="Doe", email="John@doe.com",
                                           address=Address.objects.create(
                                               line_1='Musterstraße 1',
                                               postcode='12345', city='Musterstadt',
                                               country='Germany'),
                                           vendor=self.vendor)
        second_customer = Customer.objects.create(first_name="Johnny", last_name="Doe", email="John@doe.com",
                                                  address=Address.objects.create(
                                                      line_1='Musterstraße 1',
                                                      postcode='12345', city='Musterstadt',
                                                      country='Germany'),
                                                  vendor=second_vendor)
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        customer_list = response.context_data['customer_list']
        self.assertEqual(len(customer_list), 1)
        self.assertEqual(customer_list[0], customer)
        self.assertNotIn(second_customer, customer_list)


class CustomerDeleteViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username="test", password="password")
        address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        cls.vendor = Vendor.objects.create(name="Test", company_name="Test", user=cls.user, address=address)

    @classmethod
    def tearDownClass(cls):
        Customer.objects.all().delete()
        Vendor.objects.all().delete()
        Address.objects.all().delete()
        User.objects.all().delete()

    def setUp(self):
        address = Address.objects.create(line_1="Test2", postcode="12345", city="Test", country="Germany")
        self.customer = Customer.objects.create(first_name='John', last_name='Doe', email='john@doe.com',
                                                vendor=self.vendor, address=address, )

    def tearDown(self):
        Customer.objects.all().delete()

    def test_auth_required(self):
        url = reverse("customer-delete", args=[self.customer.id])
        response = self.client.post(f"{url}", follow=True)
        self.assertRedirects(response, f"/accounts/login/?next={url}")
        self.assertEqual(Customer.objects.count(), 1)

    def test_not_own_customer_get(self):
        second_user = User.objects.create_user(username="test2", password="<PASSWORD>")
        self.client.force_login(second_user)
        url = reverse('customer-delete', args=[self.customer.id])
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/customers/')
        self.assertEqual(Customer.objects.count(), 1)

    def test_not_own_customer_post(self):
        second_user = User.objects.create_user(username="test2", password="<PASSWORD>")
        self.client.force_login(second_user)
        url = reverse('customer-delete', args=[self.customer.id])
        response = self.client.post(url, follow=True)
        self.assertRedirects(response, '/customers/')
        self.assertEqual(Customer.objects.count(), 1)

    def test_delete_customer(self):
        self.client.force_login(self.user)
        url = reverse("customer-delete", args=[self.customer.id])
        response = self.client.post(f"{url}", follow=True)
        self.assertRedirects(response, '/customers/')
        self.assertEqual(Customer.objects.count(), 0)


class CustomerModelTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username="test", password="password")

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()

    def test_long_email(self):
        long_email = 'a' * 240 + '@' + 'b' * 20 + '.com'
        address = Address.objects.create(line_1="Musterstraße 1", postcode="12345", city="Musterstadt",
                                         country="Germany")
        customer = Customer.objects.create(first_name='John', last_name='Doe', email=long_email, address=address,
                                           )
        with self.assertRaises(ValidationError):
            customer.full_clean()


class AddVendorViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username="test", password="password")

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()

    def setUp(self):
        self.url = reverse('vendor-add')

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoice/vendor_form.html')

    @given(build_vendor_fields(), build_address_fields(), build_bank_fields())
    @example(('John', 'Doe Company', 'DE123456'),
             ('Musterstraße 1', '', '', 'Musterstadt', '12345', '', 'Germany'),
             ('John Doe', 'ES9620686250804690656114', 'CAHMESMM'))
    def test_add_vendor(self, vendor_fields, address_fields, bank_fields):
        self.client.force_login(self.user)
        name, company, tax_id = vendor_fields
        address_line_1, address_line_2, address_line_3, city, postcode, state, country = address_fields
        owner, iban, bic = bank_fields
        response = self.client.post(self.url, data={
            'name': name,
            'company_name': company,
            'tax_id': tax_id,
            'line_1': address_line_1,
            'line_2': address_line_2,
            'line_3': address_line_3,
            'city': city,
            'postcode': postcode,
            'state': state,
            'country': country,
            'owner': owner,
            'iban': str(iban),
            'bic': str(bic),
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/vendors/')
        vendor = Vendor.objects.get(name=name)
        address = Address.objects.get(line_1=address_line_1)
        bank_account = BankAccount.objects.first()
        self.assertIsNotNone(vendor)
        self.assertEqual(vendor.company_name, company)
        self.assertEqual(vendor.address, address)
        self.assertEqual(vendor.bank_account, bank_account)

    def test_update_invalid_input_address(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data={
            'name': 'John',
            'company_name': 'John Doe Company',
            'line_1': '',
            'city': 'Musterstadt',
            'postcode': '12345',
            'country': 'Germany',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context_data['address_form'], 'line_1',
                             errors=['This field is required.'])

    def test_update_invalid_input_bank_account(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data={
            'name': 'John',
            'company_name': 'John Doe Company',
            'line_1': 'Musterstraße 1',
            'city': 'Musterstadt',
            'postcode': '12345',
            'country': 'Germany',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context_data['bank_form'], 'iban',
                             errors=['This field is required.'])

    def test_login_required(self):
        url = reverse("vendor-add")
        response = self.client.post(f"{url}", follow=True)
        self.assertRedirects(response, f"/accounts/login/?next={url}")


class UpdateVendorViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username="test", password="password")

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()

    def setUp(self):
        owner, iban, bic = build_bank_fields().example()
        vendor = Vendor.objects.create(name="John", company_name="Doe Company",
                                       address=Address.objects.create(
                                           line_1='Musterstraße 1',
                                           postcode='12345', city='Musterstadt',
                                           country='Germany'),
                                       bank_account=BankAccount.objects.create(owner=owner, iban=iban,
                                                                               bic=bic),
                                       user=self.user)
        self.url = reverse('vendor-update', args=[vendor.id])

    def tearDown(self):
        Vendor.objects.all().delete()

    def test_get(self):
        self.client.force_login(self.user)
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoice/vendor_form.html')

    @given(build_vendor_fields(), build_address_fields(), build_bank_fields())
    def test_update_vendor(self, vendor_fields, address_fields, bank_fields):
        name, company, tax_id = vendor_fields
        address_line_1, address_line_2, address_line_3, city, postcode, state, country = address_fields
        owner, iban, bic = bank_fields
        self.client.force_login(self.user)
        response = self.client.post(self.url, data={
            'name': name,
            'company_name': company,
            'tax_id': tax_id,
            'line_1': address_line_1,
            'line_2': address_line_2,
            'line_3': address_line_3,
            'city': city,
            'postcode': postcode,
            'state': state,
            'country': country,
            'owner': owner,
            'iban': str(iban),
            'bic': str(bic),
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/vendors/')
        vendor = Vendor.objects.get(name=name)
        address = Address.objects.get(line_1=address_line_1)
        bank_account = BankAccount.objects.first()
        self.assertIsNotNone(vendor)
        self.assertEqual(vendor.company_name, company)
        self.assertEqual(vendor.address, address)
        self.assertEqual(vendor.bank_account, bank_account)

    def test_update_invalid_input_address(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data={
            'name': 'John',
            'company_name': 'John Doe Company',
            'line_1': '',
            'city': 'Musterstadt',
            'postcode': '12345',
            'country': 'Germany', }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context_data['address_form'], 'line_1',
                             errors=['This field is required.'])

    def test_update_invalid_input_bank_account(self):
        self.client.force_login(self.user)
        response = self.client.post(self.url, data={
            'name': 'John',
            'company_name': 'John Doe Company',
            'line_1': 'Musterstraße 1',
            'city': 'Musterstadt',
            'postcode': '12345',
            'country': 'Germany', }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context_data['bank_form'], 'iban',
                             errors=['This field is required.'])

    def test_auth_required(self):
        response = self.client.post(self.url, follow=True)
        self.assertRedirects(response, f"/accounts/login/?next={self.url}")

    def test_not_own_vendor_get(self):
        second_user = User.objects.create_user(username="test2", password="<PASSWORD>")
        self.client.force_login(second_user)
        response = self.client.get(self.url, follow=True)
        self.assertRedirects(response, '/vendors/')

    def test_not_own_vendor_post(self):
        second_user = User.objects.create_user(username="test2", password="<PASSWORD>")
        self.client.force_login(second_user)
        response = self.client.post(self.url, follow=True)
        self.assertRedirects(response, '/vendors/')


class VendorListViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username="test", password="password")
        address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        cls.vendor = Vendor.objects.create(name="John", company_name="Doe Company", address=address, user=cls.user)
        cls.url = reverse('vendor-list')

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()

    def test_only_users_vendors(self):
        second_user = User.objects.create_user(username="test2", password="<PASSWORD>")
        second_address = Address.objects.create(line_1="Test2", postcode="12345", city="Test2", country="Germany")
        second_vendor = Vendor.objects.create(name="Test2", company_name="Test2", user=second_user,
                                              address=second_address)

        self.client.force_login(self.user)
        response = self.client.get(self.url)
        vendors = response.context_data['vendor_list']
        self.assertEqual(len(vendors), 1)
        self.assertEqual(vendors[0], self.vendor)
        self.assertNotIn(second_vendor, vendors)


class VendorDeleteViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username="test", password="password")
        cls.address = Address.objects.create()
        cls.vendor = Vendor.objects.create(address=cls.address, user=cls.user)

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()
        Address.objects.all().delete()
        Vendor.objects.all().delete()

    def test_auth_required(self):
        url = reverse("vendor-delete", args=[self.vendor.id])
        response = self.client.post(f"{url}", follow=True)
        self.assertRedirects(response, f"/accounts/login/?next={url}")

    def test_not_own_invoice_get(self):
        self.client.force_login(self.user)
        second_user = User.objects.create_user(username="test2", password="<PASSWORD>")
        address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor_address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor = Vendor.objects.create(name="Test22", company_name="Test22", user=second_user, address=vendor_address)
        url = reverse('vendor-delete', args=[vendor.id])
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/vendors/')
        self.assertEqual(Vendor.objects.all().count(), 2)

    def test_not_own_invoice_post(self):
        self.client.force_login(self.user)
        second_user = User.objects.create_user(username="test2", password="<PASSWORD>")

        vendor_address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor = Vendor.objects.create(name="Test22", company_name="Test22", user=second_user, address=vendor_address)

        url = reverse('vendor-delete', args=[vendor.id])
        response = self.client.post(url, data={
            'invoice_number': 2000,
        }, follow=True)
        self.assertRedirects(response, '/vendors/')
        self.assertEqual(Vendor.objects.all().count(), 2)


class BankAccountTestCase(TestCase):
    def test_bic_overwrite(self):
        user_iban = 'DE02500105170137075030'
        user_bic = 'INGDDEFF'
        bank_account = BankAccount(iban=user_iban, bic=user_bic)
        bank_account.save()
        self.assertEqual(user_iban, bank_account.iban)
        self.assertEqual('INGDDEFFXXX', bank_account.bic)

    def test_iban_input_white_space(self):
        user_iban = 'DE02 5001 0517 0137 0750 30'
        user_bic = 'INGDDEFFXXX'
        bank_account = BankAccount(iban=user_iban, bic=user_bic)
        bank_account.save()
        self.assertEqual('DE02500105170137075030', bank_account.iban)
        self.assertEqual('INGDDEFFXXX', bank_account.bic)

    def test_empty_owner(self):
        user_iban = 'DE02500105170137075030'
        user_bic = 'INGDDEFFXXX'
        bank_account = BankAccount(iban=user_iban, bic=user_bic, owner='')
        with self.assertRaises(ValidationError):
            bank_account.full_clean()

    def test_too_long_iban(self):
        user_iban = 'DE025001051701370750301'
        user_bic = 'INGDDEFFXXX'
        bank_account = BankAccount(iban=user_iban, bic=user_bic)
        with self.assertRaises(ValidationError):
            bank_account.full_clean()

    def test_too_long_bic(self):
        user_iban = 'DE02500105170137075030'
        user_bic = 'INGDDEFFXXX1'
        bank_account = BankAccount(iban=user_iban, bic=user_bic)
        with self.assertRaises(ValidationError):
            bank_account.full_clean()


class InvoiceItemModelTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username="test", password="password")

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()

    def setUp(self):
        address = Address.objects.create()
        vendor = Vendor.objects.create(address=address, user=self.user)
        customer = Customer.objects.create(address=address, vendor=vendor)
        self.invoice = Invoice.objects.create(invoice_number=1, vendor=vendor, customer=customer,
                                              date=now())

    def tearDown(self):
        InvoiceItem.objects.all().delete()
        Customer.objects.all().delete()
        Vendor.objects.all().delete()
        Address.objects.all().delete()

    @given(text(min_size=1), text(min_size=1),
           decimals(places=4, min_value=0, max_value=1000000, allow_infinity=False, allow_nan=False),
           decimals(places=2, min_value=-1000000, max_value=1000000, allow_infinity=False, allow_nan=False),
           decimals(places=4, min_value=0, max_value=1, allow_infinity=False, allow_nan=False))
    @example('Security Services', 'Implementation of a firewall', 1, HUNDRED, GERMAN_TAX_RATE)
    def test_create_invoice_item(self, name, description, quantity, price, tax):
        invoice_item = InvoiceItem(name=name, description=description, quantity=quantity,
                                   price=price, tax=tax, invoice=self.invoice)
        invoice_item.full_clean()
        self.assertEqual(invoice_item.name, name)
        self.assertEqual(invoice_item.description, description)
        self.assertEqual(invoice_item.quantity, quantity)
        self.assertEqual(invoice_item.price, price)
        self.assertEqual(invoice_item.tax, tax)
        self.assertEqual(invoice_item.net_total, price * quantity)
        self.assertEqual(invoice_item.total, price * quantity * (ONE + tax))

    def test_negative_tax(self):
        invoice_item = InvoiceItem(name='Security Services',
                                   description='Implementation of a firewall', quantity=1,
                                   price=HUNDRED, tax=-GERMAN_TAX_RATE, invoice=self.invoice)
        with self.assertRaises(ValidationError):
            invoice_item.full_clean()

    def test_high_tax(self):
        invoice_item = InvoiceItem(name='Security Services',
                                   description='Implementation of a firewall', quantity=1,
                                   price=HUNDRED, tax=Decimal('1.19'), invoice=self.invoice)
        with self.assertRaises(ValidationError):
            invoice_item.full_clean()

    def test_inf_price(self):
        invoice_item = InvoiceItem(name='Security Services',
                                   description='Implementation of a firewall', quantity=1,
                                   price=inf, tax=GERMAN_TAX_RATE, invoice=self.invoice)
        with self.assertRaises(ValidationError):
            invoice_item.full_clean()

    def test_more_then_million_price(self):
        invoice_item = InvoiceItem(name='Security Services',
                                   description='Implementation of a firewall', quantity=1,
                                   price=1000001, tax=GERMAN_TAX_RATE, invoice=self.invoice)
        with self.assertRaises(ValidationError):
            invoice_item.full_clean()

    def test_less_then_negative_million_price(self):
        invoice_item = InvoiceItem(name='Security Services',
                                   description='Implementation of a firewall', quantity=1,
                                   price=-1000001, tax=GERMAN_TAX_RATE, invoice=self.invoice)
        with self.assertRaises(ValidationError):
            invoice_item.full_clean()

    def test_nan_price(self):
        invoice_item = InvoiceItem(name='Security Services',
                                   description='Implementation of a firewall', quantity=1,
                                   price=nan, tax=Decimal, invoice=self.invoice)
        with self.assertRaises(ValidationError):
            invoice_item.full_clean()

    def test_three_digits_price(self):
        invoice_item = InvoiceItem(name='Security Services',
                                   description='Implementation of a firewall', quantity=1,
                                   price=Decimal('3.111'), tax=Decimal, invoice=self.invoice)
        with self.assertRaises(ValidationError):
            invoice_item.full_clean()

    def test_negative_quantity(self):
        invoice_item = InvoiceItem(name='Security Services',
                                   description='Implementation of a firewall', quantity=-1,
                                   price=HUNDRED, tax=GERMAN_TAX_RATE, invoice=self.invoice)
        with self.assertRaises(ValidationError):
            invoice_item.full_clean()

    def test_empty_name(self):
        invoice_item = InvoiceItem(name='',
                                   description='Implementation of a firewall', quantity=1,
                                   price=HUNDRED, tax=GERMAN_TAX_RATE, invoice=self.invoice)
        with self.assertRaises(ValidationError):
            invoice_item.full_clean()

    def test_empty_description(self):
        invoice_item = InvoiceItem(name='Security Services',
                                   description='', quantity=1,
                                   price=HUNDRED, tax=GERMAN_TAX_RATE, invoice=self.invoice)
        with self.assertRaises(ValidationError):
            invoice_item.full_clean()

    def test_list_export(self):
        invoice = Invoice()
        name = 'Concert'
        description = '2 hour live event'
        quantity = 1
        price = Decimal('4000.0')
        tax = GERMAN_TAX_RATE
        invoice_item = InvoiceItem(name=name, description=description, quantity=quantity, unit='piece',
                                   price=price, tax=tax, invoice=invoice)
        list_export = invoice_item.list_export
        self.assertEqual(list_export, [name, description, '1 piece', '4000.00 EUR', '19%', '4000.00 EUR',
                                       '4760.00 EUR'])

    def test_sql_quantity_limit(self):
        invoice = Invoice()
        name = 'Concert'
        description = '2 hour live event'
        price = Decimal('4000.0')
        tax = GERMAN_TAX_RATE
        quantity = MAX_VALUE_DJANGO_SAVE + 1
        invoice_item = InvoiceItem(name=name, description=description, quantity=quantity,
                                   price=price, tax=tax, invoice=invoice)
        with self.assertRaises(ValidationError):
            invoice_item.full_clean()

    def test_tax_string_1(self):
        invoice_item = InvoiceItem(name='',
                                   description='', quantity=1,
                                   price=HUNDRED, tax=Decimal('0.19'), invoice=self.invoice)
        self.assertEqual(invoice_item.tax_string.rstrip('%'), '19')

    def test_tax_string_2(self):
        invoice_item = InvoiceItem(name='',
                                   description='', quantity=1,
                                   price=HUNDRED, tax=Decimal('0.1925'), invoice=self.invoice)
        self.assertEqual(invoice_item.tax_string.rstrip('%'), '19.25')

    def test_tax_string_3(self):
        invoice_item = InvoiceItem(name='',
                                   description='', quantity=1,
                                   price=HUNDRED, tax=Decimal('0.074'), invoice=self.invoice)
        self.assertEqual(invoice_item.tax_string.rstrip('%'), '7.4')

    def test_tax_string_4(self):
        invoice_item = InvoiceItem(name='',
                                   description='', quantity=1,
                                   price=HUNDRED, tax=Decimal('0.07999'), invoice=self.invoice)
        self.assertEqual(invoice_item.tax_string.rstrip('%'), '8')

    def test_tax_amount(self):
        invoice_item = InvoiceItem(name='',
                                   description='', quantity=1,
                                   price=HUNDRED, tax=Decimal('0.19'), invoice=self.invoice)
        self.assertEqual(invoice_item.tax_amount, Decimal('19'))

    def test_tax_amount_low_amount(self):
        invoice_item = InvoiceItem(name='',
                                   description='', quantity=1,
                                   price=ONE, tax=Decimal('0.19'), invoice=self.invoice)
        self.assertEqual(invoice_item.tax_amount, Decimal('0.19'))

    def test_tax_amount_tiny_amount(self):
        invoice_item = InvoiceItem(name='',
                                   description='', quantity=1,
                                   price=Decimal('0.01'), tax=Decimal('0.19'), invoice=self.invoice)
        self.assertEqual(invoice_item.tax_amount, Decimal('0.0019'))

    def test_tax_amount_string(self):
        invoice_item = InvoiceItem(name='',
                                   description='', quantity=1,
                                   price=HUNDRED, tax=Decimal('0.19'), invoice=self.invoice)
        self.assertEqual(invoice_item.tax_amount_string, '19.00 EUR')

    def test_tax_amount_low_amount_string(self):
        invoice_item = InvoiceItem(name='',
                                   description='', quantity=1,
                                   price=ONE, tax=Decimal('0.19'), invoice=self.invoice)
        self.assertEqual(invoice_item.tax_amount_string, '0.19 EUR')

    def test_tax_amount_tiny_amount_string(self):
        invoice_item = InvoiceItem(name='',
                                   description='', quantity=1,
                                   price=Decimal('0.01'), tax=Decimal('0.19'), invoice=self.invoice)
        self.assertEqual(invoice_item.tax_amount_string, '0.00 EUR')


class InvoiceModelTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username="test", password="password")

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()

    def setUp(self):
        address = Address.objects.create()
        vendor = Vendor.objects.create(address=address, user=self.user)
        _ = Customer.objects.create(address=address, vendor=vendor)

    def tearDown(self):
        Vendor.objects.all().delete()
        Customer.objects.all().delete()
        Address.objects.all().delete()
        Invoice.objects.all().delete()
        InvoiceItem.objects.all().delete()

    @given(build_invoice_item())
    def test_invoice_items(self, invoice_item):
        invoice = Invoice.objects.create(invoice_number=1, vendor=Vendor.objects.first(),
                                         customer=Customer.objects.first(), date=now())
        invoice_item.invoice = invoice
        invoice_item.save()
        self.assertEqual(invoice.items, [invoice_item])

    @given(build_invoice_item())
    def test_table_export(self, invoice_item):
        invoice = Invoice.objects.create(invoice_number=1, vendor=Vendor.objects.first(),
                                         customer=Customer.objects.first(), date=now())
        invoice_item.invoice = invoice
        invoice_item.save()
        table = invoice.table_export
        self.assertEqual(table, [['Name', 'Description', 'Quantity', 'Price', 'Tax', 'Net Total', 'Total'],
                                 [invoice_item.name, invoice_item.description,
                                  invoice_item.quantity_string,
                                  invoice_item.price_string, invoice_item.tax_string,
                                  invoice_item.net_total_string, invoice_item.total_string]])

    @given(build_invoice_item(), build_invoice_item())
    def test_invoice_net_total(self, first_item, second_item):
        invoice = Invoice.objects.create(invoice_number=1, vendor=Vendor.objects.first(),
                                         customer=Customer.objects.first(), date=now())
        first_item.invoice = invoice
        second_item.invoice = invoice
        first_item.save()
        second_item.save()
        self.assertEqual(invoice.net_total, first_item.net_total + second_item.net_total,
                         msg=f'First Net Total:{first_item.net_total}'
                             f'Second Net Total:{second_item.net_total}'
                             f'Invoice Net Total:{invoice.net_total}')

    @given(build_invoice_item(), build_invoice_item())
    def test_invoice_total(self, first_item, second_item):
        invoice = Invoice.objects.create(invoice_number=1, vendor=Vendor.objects.first(),
                                         customer=Customer.objects.first(), date=now())
        first_item.invoice = invoice
        second_item.invoice = invoice
        first_item.save()
        second_item.save()
        self.assertEqual(invoice.total, first_item.total + second_item.total,
                         msg=f'First Total:{first_item.total}\n'
                             f'Second Total:{second_item.total}\n'
                             f'Invoice Total:{invoice.total}')

    def test_no_items_net_total(self):
        invoice = Invoice.objects.create(invoice_number=1, vendor=Vendor.objects.first(),
                                         customer=Customer.objects.first(), date=now())
        self.assertEqual(invoice.net_total, 0)

    def test_no_items_total(self):
        invoice = Invoice.objects.create(invoice_number=1, vendor=Vendor.objects.first(),
                                         customer=Customer.objects.first(), date=now())
        self.assertEqual(invoice.total, 0)

    def test_due_date_after_date(self):
        date = now()
        due_date = date - timedelta(days=1)
        invoice = Invoice(invoice_number=1, vendor=Vendor.objects.first(),
                          customer=Customer.objects.first(), date=date, due_date=due_date)
        with self.assertRaises(ValidationError):
            invoice.validate_constraints()

    def test_due_date_before_date(self):
        date = now()
        due_date = date + timedelta(days=1)
        invoice = Invoice.objects.create(invoice_number=1, vendor=Vendor.objects.first(),
                                         customer=Customer.objects.first(), date=date, due_date=due_date)
        invoice.full_clean()

    def test_due_date_equal_date(self):
        date = now()
        due_date = date
        invoice = Invoice.objects.create(invoice_number=1, vendor=Vendor.objects.first(),
                                         customer=Customer.objects.first(), date=date, due_date=due_date)
        invoice.full_clean()

    def test_paid(self):
        invoice = Invoice.objects.create(invoice_number=1, vendor=Vendor.objects.first(),
                                         customer=Customer.objects.first(), date=now())
        self.assertEqual(invoice.paid, False)
        invoice.paid = True
        invoice.save()
        retrieve_invoice = Invoice.objects.get(invoice_number=1)
        self.assertEqual(retrieve_invoice.paid, True)

    @given(lists(build_invoice_item(), min_size=1, max_size=100))
    def test_correct_sum(self, invoice_items):
        due_date = date = now()
        invoice = Invoice.objects.create(invoice_number=1, vendor=Vendor.objects.first(),
                                         customer=Customer.objects.first(), date=date, due_date=due_date)
        for item in invoice_items:
            item.invoice = invoice
            item.save()

        # high precision, internal representation
        self.assertEqual(invoice.net_total + invoice.tax_amount, invoice.total)

        # rounded to two decimals, customers expect this to be equal:
        self.assertEqual(invoice.net_total_rounded + invoice.tax_amount_rounded, invoice.total_rounded)

    def test_sum_tiny_vat(self):
        date = now()
        due_date = date
        invoice = Invoice.objects.create(invoice_number=1, vendor=Vendor.objects.first(),
                                         customer=Customer.objects.first(), date=date, due_date=due_date)
        for _ in range(100):
            InvoiceItem.objects.create(invoice=invoice, name='', description='', quantity=1, price=Decimal('0.01'),
                                       tax=Decimal('0.19'))
        self.assertEqual(invoice.net_total, Decimal('1'))
        self.assertEqual(invoice.tax_amount, Decimal('0.19'))
        self.assertEqual(invoice.total, Decimal('1.19'))
        self.assertEqual(invoice.net_total_string, f'1.00 EUR')
        self.assertEqual(invoice.tax_amount_strings, {'19%': f'0.19 EUR'})
        self.assertEqual(invoice.total_string, f'1.19 EUR')

    def test_save_final_model_on_creation(self):
        invoice = Invoice.objects.create(invoice_number=1, vendor=Vendor.objects.first(),
                                         customer=Customer.objects.first(), date=now(), final=True)
        self.assertTrue(invoice.final)

    def test_save_after_final_model(self):
        invoice = Invoice.objects.create(invoice_number=1, vendor=Vendor.objects.first(),
                                         customer=Customer.objects.first(), date=now(), final=True)
        invoice.invoice_number = 2
        with self.assertRaises(FinalError):
            invoice.save()

    def test_tax_amount_per_rate(self):
        date = now()
        due_date = date
        invoice = Invoice.objects.create(invoice_number=1, vendor=Vendor.objects.first(),
                                         customer=Customer.objects.first(), date=date, due_date=due_date)
        InvoiceItem.objects.create(invoice=invoice, name='', description='', quantity=1, price=Decimal('100'),
                                   tax=Decimal('0.19'))
        InvoiceItem.objects.create(invoice=invoice, name='', description='', quantity=1, price=Decimal('100'),
                                   tax=Decimal('0.07'))
        self.assertEqual(invoice.tax_amount_per_rate, {'19%': Decimal('19'), '7%': Decimal('7')})

    def test_tax_amount_strings(self):
        date = now()
        due_date = date
        invoice = Invoice.objects.create(invoice_number=1, vendor=Vendor.objects.first(),
                                         customer=Customer.objects.first(), date=date, due_date=due_date)
        InvoiceItem.objects.create(invoice=invoice, name='', description='', quantity=1, price=Decimal('100'),
                                   tax=Decimal('0.19'))
        InvoiceItem.objects.create(invoice=invoice, name='', description='', quantity=1, price=Decimal('100'),
                                   tax=Decimal('0.07'))
        self.assertEqual(invoice.tax_amount_strings, {'19%': '19.00 EUR', '7%': '7.00 EUR'})

    def test_tax_amount_strings_exclude_zero_rate(self):
        date = now()
        due_date = date
        invoice = Invoice.objects.create(invoice_number=1, vendor=Vendor.objects.first(),
                                         customer=Customer.objects.first(), date=date, due_date=due_date)
        InvoiceItem.objects.create(invoice=invoice, name='', description='', quantity=1, price=Decimal('100'),
                                   tax=Decimal('0.19'))
        InvoiceItem.objects.create(invoice=invoice, name='', description='', quantity=1, price=Decimal('100'),
                                   tax=Decimal('0'))
        self.assertEqual(invoice.tax_amount_strings, {'19%': '19.00 EUR'})

    def test_invoice_items_without_save(self):
        invoice = Invoice(invoice_number=1, vendor=Vendor.objects.first(),
                          customer=Customer.objects.first(), date=now())
        self.assertEqual(len(invoice.items), 0)


class InvoicePDFViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username="test", password="password")

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()

    def setUp(self):
        address = Address.objects.create()
        vendor = Vendor.objects.create(address=address, user=self.user)
        customer = Customer.objects.create(address=address, vendor=vendor)
        self.invoice = Invoice.objects.create(invoice_number=1, vendor=vendor,
                                              customer=customer, date=now())

    def test_pdf(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse('invoice-pdf', kwargs={'invoice_id': self.invoice.pk}), follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get('Content-Type'), 'application/pdf')
        self.assertEqual(response.status_code, 200)

    def test_unauthorized(self):
        self.client.logout()
        response = self.client.get(reverse('invoice-pdf', kwargs={'invoice_id': self.invoice.pk}), follow=True)
        self.assertRedirects(response, f'/accounts/login/?next=/invoice/{self.invoice.pk}/pdf/')

    def test_forbidden(self):
        second_user = User.objects.create_user(username="test2", password="password")
        self.client.force_login(second_user)
        response = self.client.get(reverse('invoice-pdf', kwargs={'invoice_id': self.invoice.pk}))
        self.assertEqual(response.status_code, 403)


class InvoiceListViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username="test", password="password")
        cls.url = reverse('invoice-list')
        cls.address = Address.objects.create()
        cls.vendor = Vendor.objects.create(address=cls.address, user=cls.user)

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()
        Address.objects.all().delete()

    def test_only_users_invoices(self):
        second_address = Address.objects.create()
        customer = Customer.objects.create(vendor=self.vendor, address=self.address)
        second_user = User.objects.create_user(username="test2", password="password")
        second_vendor = Vendor.objects.create(user=second_user, address=second_address)
        self.client.force_login(self.user)
        invoice = Invoice.objects.create(invoice_number=1, vendor=self.vendor, date=now(),
                                         customer=customer)
        second_invoice = Invoice.objects.create(invoice_number=2, vendor=second_vendor, date=now(),
                                                customer=customer)
        response = self.client.get(self.url)
        invoice_list = response.context_data['invoice_list']
        self.assertEqual(len(invoice_list), 1)
        self.assertEqual(invoice_list[0], invoice)
        self.assertNotIn(second_invoice, invoice_list)


class InvoiceUpdateViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username="test", password="password")
        cls.address = Address.objects.create()
        cls.vendor = Vendor.objects.create(address=cls.address, user=cls.user)
        cls.customer = Customer.objects.create(vendor=cls.vendor, address=cls.address)

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()
        Address.objects.all().delete()
        Vendor.objects.all().delete()

    def setUp(self):
        self.invoice = Invoice.objects.create(invoice_number=1, vendor=self.vendor, date=now(),
                                              customer=self.customer)

    def test_auth_required(self):
        url = reverse("invoice-update", args=[self.invoice.id])
        response = self.client.post(f"{url}", follow=True)
        self.assertRedirects(response, f"/accounts/login/?next={url}")

    def test_not_own_invoice_get(self):
        self.client.force_login(self.user)
        second_user = User.objects.create_user(username="test2", password="<PASSWORD>")
        address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor_address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor = Vendor.objects.create(name="Test22", company_name="Test22", user=second_user, address=vendor_address)
        customer = Customer.objects.create(first_name="John", last_name="Doe", email="John@doe.com", address=address,
                                           vendor=vendor)
        invoice = Invoice.objects.create(invoice_number=1, vendor=vendor, date=now(), customer=customer)
        url = reverse('invoice-update', args=[invoice.id])
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/invoices/')

    def test_not_own_invoice_post(self):
        self.client.force_login(self.user)
        second_user = User.objects.create_user(username="test2", password="<PASSWORD>")

        address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor_address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor = Vendor.objects.create(name="Test22", company_name="Test22", user=second_user, address=vendor_address)
        customer = Customer.objects.create(first_name="John", last_name="Doe", email="John@doe.com", address=address,
                                           vendor=vendor)
        invoice = Invoice.objects.create(invoice_number=1, vendor=vendor, date=now(), customer=customer)

        url = reverse('invoice-update', args=[invoice.id])
        response = self.client.post(url, data={
            'invoice_number': 2000,
        }, follow=True)
        self.assertRedirects(response, '/invoices/')


class InvoicePaidViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username="test", password="password")
        cls.address = Address.objects.create()
        cls.vendor = Vendor.objects.create(address=cls.address, user=cls.user)
        cls.customer = Customer.objects.create(vendor=cls.vendor, address=cls.address)

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()
        Address.objects.all().delete()
        Vendor.objects.all().delete()

    def setUp(self):
        self.invoice = Invoice.objects.create(invoice_number=1, vendor=self.vendor, date=now(),
                                              customer=self.customer)

    def test_auth_required(self):
        url = reverse("invoice-paid", args=[self.invoice.id])
        response = self.client.post(f"{url}", follow=True)
        self.assertRedirects(response, f"/accounts/login/?next={url}")

    def test_not_own_invoice_get(self):
        self.client.force_login(self.user)
        second_user = User.objects.create_user(username="test2", password="<PASSWORD>")
        address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor_address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor = Vendor.objects.create(name="Test22", company_name="Test22", user=second_user, address=vendor_address)
        customer = Customer.objects.create(first_name="John", last_name="Doe", email="John@doe.com", address=address,
                                           vendor=vendor)
        invoice = Invoice.objects.create(invoice_number=1, vendor=vendor, date=now(), customer=customer)
        url = reverse('invoice-paid', args=[invoice.id])
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/invoices/')

    def test_not_own_invoice_post(self):
        self.client.force_login(self.user)
        second_user = User.objects.create_user(username="test2", password="<PASSWORD>")

        address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor_address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor = Vendor.objects.create(name="Test22", company_name="Test22", user=second_user, address=vendor_address)
        customer = Customer.objects.create(first_name="John", last_name="Doe", email="John@doe.com", address=address,
                                           vendor=vendor)
        invoice = Invoice.objects.create(invoice_number=1, vendor=vendor, date=now(), customer=customer)

        url = reverse('invoice-paid', args=[invoice.id])
        response = self.client.post(url, data={
            'invoice_number': 2000,
        }, follow=True)
        self.assertRedirects(response, '/invoices/')


class InvoiceDeleteViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username="test", password="password")
        cls.address = Address.objects.create()
        cls.vendor = Vendor.objects.create(address=cls.address, user=cls.user)
        cls.customer = Customer.objects.create(vendor=cls.vendor, address=cls.address)

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()
        Address.objects.all().delete()
        Vendor.objects.all().delete()

    def setUp(self):
        self.invoice = Invoice.objects.create(invoice_number=1, vendor=self.vendor, date=now(),
                                              customer=self.customer)

    def test_auth_required(self):
        url = reverse("invoice-delete", args=[self.invoice.id])
        response = self.client.post(f"{url}", follow=True)
        self.assertRedirects(response, f"/accounts/login/?next={url}")

    def test_not_own_invoice_get(self):
        self.client.force_login(self.user)
        second_user = User.objects.create_user(username="test2", password="<PASSWORD>")
        address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor_address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor = Vendor.objects.create(name="Test22", company_name="Test22", user=second_user, address=vendor_address)
        customer = Customer.objects.create(first_name="John", last_name="Doe", email="John@doe.com", address=address,
                                           vendor=vendor)
        invoice = Invoice.objects.create(invoice_number=1, vendor=vendor, date=now(), customer=customer)
        url = reverse('invoice-delete', args=[invoice.id])
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/invoices/')
        self.assertEqual(Invoice.objects.all().count(), 2)

    def test_not_own_invoice_post(self):
        self.client.force_login(self.user)
        second_user = User.objects.create_user(username="test2", password="<PASSWORD>")

        address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor_address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor = Vendor.objects.create(name="Test22", company_name="Test22", user=second_user, address=vendor_address)
        customer = Customer.objects.create(first_name="John", last_name="Doe", email="John@doe.com", address=address,
                                           vendor=vendor)
        invoice = Invoice.objects.create(invoice_number=1, vendor=vendor, date=now(), customer=customer)

        url = reverse('invoice-delete', args=[invoice.id])
        response = self.client.post(url, data={
            'invoice_number': 2000,
        }, follow=True)
        self.assertRedirects(response, '/invoices/')
        self.assertEqual(Invoice.objects.all().count(), 2)


class InvoiceItemCreateViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username="test", password="password")
        cls.address = Address.objects.create()
        cls.vendor = Vendor.objects.create(address=cls.address, user=cls.user)
        cls.customer = Customer.objects.create(vendor=cls.vendor, address=cls.address)

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()
        Address.objects.all().delete()
        Vendor.objects.all().delete()

    def setUp(self):
        self.invoice = Invoice.objects.create(invoice_number=1, vendor=self.vendor, date=now(),
                                              customer=self.customer)

    def test_post(self):
        self.client.force_login(self.user)
        url = reverse('invoice-item-add', args=[self.invoice.id])
        response = self.client.post(url, data={
            'name': 'Work', 'description': 'Hard', 'quantity': 1, 'unit': 'Hour', 'price': 1000, 'tax': 0.19
        }, follow=True)
        self.assertRedirects(response, f'/invoice/{self.invoice.id}/')
        self.assertEqual(InvoiceItem.objects.all().count(), 1)

    def test_auth_required(self):
        url = reverse("invoice-item-add", args=[self.invoice.id])
        response = self.client.post(f"{url}", follow=True)
        self.assertRedirects(response, f"/accounts/login/?next={url}")
        self.assertEqual(InvoiceItem.objects.all().count(), 0)

    def test_not_own_invoice_get(self):
        self.client.force_login(self.user)
        second_user = User.objects.create_user(username="test2", password="<PASSWORD>")
        address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor_address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor = Vendor.objects.create(name="Test22", company_name="Test22", user=second_user, address=vendor_address)
        customer = Customer.objects.create(first_name="John", last_name="Doe", email="John@doe.com", address=address,
                                           vendor=vendor)
        invoice = Invoice.objects.create(invoice_number=1, vendor=vendor, date=now(), customer=customer)
        url = reverse('invoice-item-add', args=[invoice.id])
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/invoices/')
        self.assertEqual(InvoiceItem.objects.all().count(), 0)

    def test_not_own_invoice_post(self):
        self.client.force_login(self.user)
        second_user = User.objects.create_user(username="test2", password="<PASSWORD>")

        address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor_address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor = Vendor.objects.create(name="Test22", company_name="Test22", user=second_user, address=vendor_address)
        customer = Customer.objects.create(first_name="John", last_name="Doe", email="John@doe.com", address=address,
                                           vendor=vendor)
        invoice = Invoice.objects.create(invoice_number=1, vendor=vendor, date=now(), customer=customer)

        url = reverse('invoice-item-add', args=[invoice.id])
        response = self.client.post(url, data={
            'name': 'Work', 'description': 'Hard', 'quantity': 1, 'unit': 'Hour', 'price': 1000, 'tax': 0.19
        }, follow=True)
        self.assertRedirects(response, '/invoices/')
        self.assertEqual(InvoiceItem.objects.all().count(), 0)


class InvoiceItemUpdateViewTestCase(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.user = User.objects.create_user(username="test", password="password")
        cls.address = Address.objects.create()
        cls.vendor = Vendor.objects.create(address=cls.address, user=cls.user)
        cls.customer = Customer.objects.create(vendor=cls.vendor, address=cls.address)

    @classmethod
    def tearDownClass(cls):
        User.objects.all().delete()
        Address.objects.all().delete()
        Vendor.objects.all().delete()

    def setUp(self):
        self.invoice = Invoice.objects.create(invoice_number=1, vendor=self.vendor, date=now(),
                                              customer=self.customer)
        self.item = InvoiceItem.objects.create(name='Work', description='Hard', quantity=1, unit='Hour', price=1000,
                                               tax=0.19, invoice=self.invoice)

    def tearDown(self):
        InvoiceItem.objects.all().delete()
        Invoice.objects.all().delete()

    def test_post(self):
        self.client.force_login(self.user)
        url = reverse('invoice-item-update', args=[self.invoice.id, self.item.id])
        data = {'name': 'Party', 'description': self.item.description, 'quantity': self.item.quantity,
                'unit': self.item.unit, 'price': self.item.price, 'tax': self.item.tax}
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(InvoiceItem.objects.get().name, 'Party')

    def test_auth_required(self):
        url = reverse('invoice-item-update', args=[self.invoice.id, self.item.id])
        data = {'name': 'Party', 'description': self.item.description, 'quantity': self.item.quantity,
                'unit': self.item.unit, 'price': self.item.price, 'tax': self.item.tax}
        response = self.client.post(url, data=data, follow=True)
        self.assertRedirects(response, f"/accounts/login/?next={url}")
        self.assertEqual(InvoiceItem.objects.get().name, 'Work')

    def test_not_own_invoice_get(self):
        self.client.force_login(self.user)
        second_user = User.objects.create_user(username="test2", password="<PASSWORD>")
        address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor_address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor = Vendor.objects.create(name="Test22", company_name="Test22", user=second_user, address=vendor_address)
        customer = Customer.objects.create(first_name="John", last_name="Doe", email="John@doe.com", address=address,
                                           vendor=vendor)
        invoice = Invoice.objects.create(invoice_number=1, vendor=vendor, date=now(), customer=customer)
        item = InvoiceItem.objects.create(name='Work', description='Hard', quantity=1, unit='Hour', price=1000,
                                          tax=0.19, invoice=invoice)
        url = reverse('invoice-item-update', args=[invoice.id, item.id])
        response = self.client.get(url, follow=True)
        self.assertRedirects(response, '/invoices/')

    def test_not_own_invoice_post(self):
        self.client.force_login(self.user)
        second_user = User.objects.create_user(username="test2", password="<PASSWORD>")

        address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor_address = Address.objects.create(line_1="Test", postcode="12345", city="Test", country="Germany")
        vendor = Vendor.objects.create(name="Test22", company_name="Test22", user=second_user, address=vendor_address)
        customer = Customer.objects.create(first_name="John", last_name="Doe", email="John@doe.com", address=address,
                                           vendor=vendor)
        invoice = Invoice.objects.create(invoice_number=1, vendor=vendor, date=now(), customer=customer)
        item = InvoiceItem.objects.create(name='Work', description='Hard', quantity=1, unit='Hour', price=1000,
                                          tax=0.19, invoice=invoice)
        data = {'name': 'Party', 'description': item.description, 'quantity': item.quantity,
                'unit': item.unit, 'price': item.price, 'tax': item.tax}
        url = reverse('invoice-item-update', args=[invoice.id, item.id])
        response = self.client.post(url, data=data, follow=True)
        self.assertRedirects(response, '/invoices/')
        self.assertEqual(InvoiceItem.objects.get(invoice_id=invoice.id).name, 'Work')


class AddInvoiceTestCase(TestCase):
    def test_login_required(self):
        url = reverse("invoice-add")
        response = self.client.post(f"{url}", follow=True)
        self.assertRedirects(response, f"/accounts/login/?next={url}")
