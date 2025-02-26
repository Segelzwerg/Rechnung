# Generated by Django 5.1.3 on 2024-12-03 09:34

from decimal import Decimal

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models

import invoice.models


class Migration(migrations.Migration):
    dependencies = [
        ('invoice', '0030_merge_20241202_1221'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='address',
            options={'verbose_name': 'address', 'verbose_name_plural': 'addresses'},
        ),
        migrations.AlterModelOptions(
            name='bankaccount',
            options={'verbose_name': 'bank account', 'verbose_name_plural': 'bank accounts'},
        ),
        migrations.AlterModelOptions(
            name='customer',
            options={'verbose_name': 'customer', 'verbose_name_plural': 'customers'},
        ),
        migrations.AlterModelOptions(
            name='invoice',
            options={'verbose_name': 'invoice', 'verbose_name_plural': 'invoices'},
        ),
        migrations.AlterModelOptions(
            name='vendor',
            options={'verbose_name': 'vendor', 'verbose_name_plural': 'vendors'},
        ),
        migrations.AlterField(
            model_name='address',
            name='city',
            field=models.CharField(max_length=120, verbose_name='city'),
        ),
        migrations.AlterField(
            model_name='address',
            name='country',
            field=models.CharField(max_length=120, verbose_name='country'),
        ),
        migrations.AlterField(
            model_name='address',
            name='line_1',
            field=models.CharField(max_length=200, verbose_name='first address line'),
        ),
        migrations.AlterField(
            model_name='address',
            name='line_2',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='second address line'),
        ),
        migrations.AlterField(
            model_name='address',
            name='line_3',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='third address line'),
        ),
        migrations.AlterField(
            model_name='address',
            name='postcode',
            field=models.CharField(max_length=10, verbose_name='postcode'),
        ),
        migrations.AlterField(
            model_name='address',
            name='state',
            field=models.CharField(blank=True, max_length=200, null=True, verbose_name='state'),
        ),
        migrations.AlterField(
            model_name='bankaccount',
            name='bic',
            field=models.CharField(max_length=11, validators=[invoice.models.validate_bic], verbose_name='BIC'),
        ),
        migrations.AlterField(
            model_name='bankaccount',
            name='iban',
            field=models.CharField(max_length=34, validators=[invoice.models.validate_iban], verbose_name='IBAN'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='address',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='invoice.address',
                                       verbose_name='address'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='email',
            field=models.EmailField(max_length=256, verbose_name='email'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='first_name',
            field=models.CharField(max_length=120, verbose_name='first name'),
        ),
        migrations.AlterField(
            model_name='customer',
            name='last_name',
            field=models.CharField(max_length=120, verbose_name='last name'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='currency',
            field=models.CharField(
                choices=[('EUR', 'Euro'), ('USD', 'US Dollar'), ('JPY', 'Japanese Yen'), ('GBP', 'Pound Sterling'),
                         ('CHF', 'Swiss Franc'), ('CAD', 'Canadian Dollar'), ('AUD', 'Australian Dollar'),
                         ('NZD', 'New Zealand Dollar'), ('SEK', 'Swedish Krona'), ('DKK', 'Danish Krone'),
                         ('NOK', 'Norwegian Krone'), ('HKD', 'Hong Kong Dollar'), ('CNY', 'Chinese Yuan')],
                default='EUR', max_length=3, verbose_name='currency'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='invoice.customer',
                                    verbose_name='customer'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='date',
            field=models.DateField(verbose_name='date'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='due_date',
            field=models.DateField(blank=True, null=True, verbose_name='due date'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='invoice_number',
            field=models.IntegerField(validators=[django.core.validators.MaxValueValidator(2147483647)],
                                      verbose_name='invoice number'),
        ),
        migrations.AlterField(
            model_name='invoice',
            name='vendor',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='invoice.vendor',
                                    verbose_name='vendor'),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='description',
            field=models.CharField(max_length=1000, verbose_name='description'),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='invoice',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='invoice.invoice',
                                    verbose_name='invoice'),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='name',
            field=models.CharField(max_length=120, verbose_name='invoice item'),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=19,
                                      validators=[django.core.validators.MinValueValidator(Decimal('-1000000.00')),
                                                  django.core.validators.MaxValueValidator(Decimal('1000000.00'))],
                                      verbose_name='price'),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='quantity',
            field=models.DecimalField(decimal_places=4, max_digits=19,
                                      validators=[django.core.validators.MinValueValidator(Decimal('0.0000')),
                                                  django.core.validators.MaxValueValidator(Decimal('1000000.0000'))],
                                      verbose_name='quantity'),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='tax',
            field=models.DecimalField(decimal_places=4, max_digits=5,
                                      validators=[django.core.validators.MinValueValidator(Decimal('0.0000')),
                                                  django.core.validators.MaxValueValidator(Decimal('1.0000'))],
                                      verbose_name='tax rate'),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='address',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='invoice.address',
                                       verbose_name='address'),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='bank_account',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                       to='invoice.bankaccount', verbose_name='bank account'),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='company_name',
            field=models.CharField(blank=True, max_length=255, null=True, verbose_name='company name'),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='name',
            field=models.CharField(max_length=255, verbose_name='name'),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='tax_id',
            field=models.CharField(blank=True, max_length=120, null=True, verbose_name='tax ID'),
        ),
    ]
