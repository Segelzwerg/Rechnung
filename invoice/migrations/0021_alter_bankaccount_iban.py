# Generated by Django 5.1.3 on 2024-11-27 14:51

from django.db import migrations, models

import invoice.models


class Migration(migrations.Migration):
    dependencies = [
        ('invoice', '0020_alter_vendor_address_alter_vendor_bank_account'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankaccount',
            name='iban',
            field=models.CharField(max_length=34, validators=[invoice.models.validate_iban]),
        ),
    ]