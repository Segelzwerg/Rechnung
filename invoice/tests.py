from datetime import timedelta
from decimal import Decimal
from math import inf, nan

import schwifty
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
    def setUp(self):
        self.url = reverse('customer-add')

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoice/customer_form.html')

    @given(build_customer_fields(), build_address_fields())
    @example(('John', 'Doe', 'john@doe.com'),
             ('Musterstraße 1', '', '', 'Musterstadt', '12345', '', 'Germany'))
    def test_add_customer(self, customer_fields, address_fields):
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
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/customers/')
        customer = Customer.objects.get(first_name=first_name, last_name=last_name)
        address = Address.objects.first()
        self.assertIsNotNone(customer)
        self.assertIsNotNone(address)
        self.assertEqual(customer.email, email)
        self.assertEqual(customer.address, address)

    def test_update_invalid_input_address(self):
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


class UpdateCustomerViewTestCase(TestCase):
    def setUp(self):
        customer = Customer.objects.create(first_name="John", last_name="Doe", email="John@doe.com",
                                           address=Address.objects.create(
                                               line_1='Musterstraße 1',
                                               postcode='12345', city='Musterstadt',
                                               country='Germany'))
        self.url = reverse('customer-update', args=[customer.id])

    def tearDown(self):
        Customer.objects.all().delete()

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoice/customer_form.html')

    @given(build_customer_fields(), build_address_fields())
    def test_update_vendor(self, customer_fields, address_fields):
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
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/customers/')
        customer = Customer.objects.get(first_name=first_name, last_name=last_name)
        address = Address.objects.first()
        self.assertIsNotNone(customer)
        self.assertEqual(customer.email, email)
        self.assertEqual(customer.address, address)

    def test_update_invalid_input_customer(self):
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


class CustomerModelTestCase(TestCase):
    def test_long_email(self):
        long_email = 'a' * 240 + '@' + 'b' * 20 + '.com'
        address = Address.objects.create(line_1="Musterstraße 1", postcode="12345", city="Musterstadt",
                                         country="Germany")
        customer = Customer.objects.create(first_name='John', last_name='Doe', email=long_email, address=address)
        with self.assertRaises(ValidationError):
            customer.full_clean()


class AddVendorViewTestCase(TestCase):
    def setUp(self):
        self.url = reverse('vendor-add')

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoice/vendor_form.html')

    @given(build_vendor_fields(), build_address_fields(), build_bank_fields())
    @example(('John', 'Doe Company', 'DE123456'),
             ('Musterstraße 1', '', '', 'Musterstadt', '12345', '', 'Germany'),
             ('John Doe', 'ES9620686250804690656114', 'CAHMESMM'))
    def test_add_vendor(self, vendor_fields, address_fields, bank_fields):
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
        address = Address.objects.first()
        bank_account = BankAccount.objects.first()
        self.assertIsNotNone(vendor)
        self.assertEqual(vendor.company_name, company)
        self.assertEqual(vendor.address, address)
        self.assertEqual(vendor.bank_account, bank_account)

    def test_update_invalid_input_address(self):
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


class UpdateVendorViewTestCase(TestCase):
    def setUp(self):
        owner, iban, bic = build_bank_fields().example()
        vendor = Vendor.objects.create(name="John", company_name="Doe Company",
                                       address=Address.objects.create(
                                           line_1='Musterstraße 1',
                                           postcode='12345', city='Musterstadt',
                                           country='Germany'),
                                       bank_account=BankAccount.objects.create(owner=owner, iban=iban,
                                                                               bic=bic))
        self.url = reverse('vendor-update', args=[vendor.id])

    def tearDown(self):
        Vendor.objects.all().delete()

    def test_get(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'invoice/vendor_form.html')

    @given(build_vendor_fields(), build_address_fields(), build_bank_fields())
    def test_update_vendor(self, vendor_fields, address_fields, bank_fields):
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
        address = Address.objects.first()
        bank_account = BankAccount.objects.first()
        self.assertIsNotNone(vendor)
        self.assertEqual(vendor.company_name, company)
        self.assertEqual(vendor.address, address)
        self.assertEqual(vendor.bank_account, bank_account)

    def test_update_invalid_input_address(self):
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
    def setUp(self):
        address = Address.objects.create()
        vendor = Vendor.objects.create(address=address)
        customer = Customer.objects.create(address=address)
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
    def setUp(self):
        address = Address.objects.create()
        _ = Vendor.objects.create(address=address)
        _ = Customer.objects.create(address=address)

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

class InvoicePDFViewTestCase(TestCase):
    def setUp(self):
        address = Address.objects.create()
        vendor = Vendor.objects.create(address=Address.objects.first())
        customer = Customer.objects.create(address=Address.objects.first())
        self.invoice = Invoice.objects.create(invoice_number=1, vendor=Vendor.objects.first(),
                                              customer=Customer.objects.first(), date=now())

    def test_pdf(self):
        response = self.client.get(reverse('invoice-pdf', kwargs={'invoice_id': self.invoice.pk}))
        self.assertEqual(response.status_code, 200)
