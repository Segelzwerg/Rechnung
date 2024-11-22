from decimal import Decimal
from math import inf, nan

from django.core.exceptions import ValidationError
from django.urls import reverse
from django.utils.timezone import now
from hypothesis import given, example
from hypothesis.extra.django import TestCase
from hypothesis.provisional import domains
from hypothesis.strategies import characters, text, emails, integers, composite, decimals

from invoice.models import Address, Customer, Vendor, InvoiceItem, Invoice, MAX_VALUE_DJANGO_SAVE

GERMAN_TAX_RATE = Decimal('0.19')
HUNDRED = Decimal('100')
ONE = Decimal('1')


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
           emails(domains=domains(max_length=255, max_element_length=63)))
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
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/customers/')
        customer = Customer.objects.get(first_name=first_name, last_name=last_name)
        self.assertIsNotNone(customer)
        self.assertEqual(customer.email, email)
        self.assertEqual(customer.address, address)


class CustomerModelTestCase(TestCase):
    def test_long_email(self):
        long_email = 'a' * 240 + '@' + 'b' * 20 + '.com'
        address = Address.objects.create(street="Main Street", number="45", city="Capital",
                                         country="Mainland")
        customer = Customer.objects.create(first_name='John', last_name='Doe', email=long_email,
                                           address=address)
        with self.assertRaises(ValidationError):
            customer.full_clean()


class AddVendorViewTestCase(TestCase):
    def setUp(self):
        self.url = reverse('vendor-add')

    @given(text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd']), min_size=1),
           text(alphabet=characters(codec='utf-8', categories=['Lu', 'Ll', 'Nd']), min_size=1),
           )
    @example("John", "Doe Company")
    def test_add_vendor(self, name, company):
        address = Address.objects.create(street="Main Street", number="45", city="Capital",
                                         country="Mainland")
        response = self.client.post(self.url, data={
            'name': name,
            'company_name': company,
            'address': 1
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertRedirects(response, '/vendors/')
        vendor = Vendor.objects.get(name=name)
        self.assertIsNotNone(vendor)
        self.assertEqual(vendor.company_name, company)
        self.assertEqual(vendor.address, address)


@composite
def build_invoice_item(draw):
    name = draw(text())
    description = draw(text())
    quantity = draw(integers(min_value=0, max_value=MAX_VALUE_DJANGO_SAVE))
    price = draw(decimals(max_value=10000000, min_value=-1000000,
                          places=2, allow_infinity=False, allow_nan=False))
    tax = draw(decimals(places=2, min_value=Decimal('0.0'), max_value=ONE))
    return InvoiceItem(name=name, description=description, quantity=quantity,
                       price=price, tax=tax)


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
           integers(min_value=1, max_value=MAX_VALUE_DJANGO_SAVE),
           decimals(allow_infinity=False, allow_nan=False, min_value=-1000000, max_value=1000000,
                    places=2),
           decimals(places=2, min_value=0.0, max_value=1.0))
    @example('Security Services', 'Implementation of a firewall', 1, HUNDRED,
             GERMAN_TAX_RATE)
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
        invoice_item = InvoiceItem(name=name, description=description, quantity=quantity,
                                   price=price, tax=tax, invoice=invoice)
        list_export = invoice_item.list_export
        self.assertEqual(list_export, [name, description, quantity, price, str(tax * 100) + '%',
                                       price * quantity, price * quantity * (ONE + tax)])

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

    @given(build_invoice_item())
    def test_tax_string(self, invoice_item: InvoiceItem):
        self.assertEqual(invoice_item.tax_string, str(invoice_item.tax * 100) + '%')


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
        self.assertEqual(table,
                         [['Name', 'Description', 'Quantity', 'Price', 'Tax', 'Net Total', 'Total'],
                          [invoice_item.name, invoice_item.description, invoice_item.quantity,
                           invoice_item.price, invoice_item.tax_string, invoice_item.net_total,
                           invoice_item.total]])

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
