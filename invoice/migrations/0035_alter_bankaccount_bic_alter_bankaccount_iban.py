# Generated by Django 5.1.3 on 2024-12-06 13:16

from django.db import migrations, models

import invoice.models


class Migration(migrations.Migration):
    dependencies = [
        ('invoice', '0034_merge_20241206_1227'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bankaccount',
            name='bic',
            field=models.CharField(max_length=120, validators=[invoice.models.validate_bic]),
        ),
        migrations.AlterField(
            model_name='bankaccount',
            name='iban',
            field=models.CharField(max_length=120, validators=[invoice.models.validate_iban]),
        ),
    ]
