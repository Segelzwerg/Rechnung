# Generated by Django 5.1.3 on 2024-11-22 09:47

import django.core.validators
from django.db import migrations, models

import invoice.models


class Migration(migrations.Migration):
    dependencies = [
        ('invoice', '0008_alter_customer_email'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='email',
            field=models.EmailField(max_length=256),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='price',
            field=models.DecimalField(decimal_places=2, max_digits=19, validators=[
                django.core.validators.MinValueValidator(-1000000),
                django.core.validators.MaxValueValidator(1000000),
                invoice.models.validate_real_values]),
        ),
        migrations.AlterField(
            model_name='invoiceitem',
            name='tax',
            field=models.DecimalField(decimal_places=2, max_digits=3,
                                      validators=[django.core.validators.MinValueValidator(0.0),
                                                  django.core.validators.MaxValueValidator(1.0)]),
        ),
    ]
