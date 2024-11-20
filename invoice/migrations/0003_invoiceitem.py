# Generated by Django 5.1.3 on 2024-11-20 09:36

import django.core.validators
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('invoice', '0002_customer_invoice'),
    ]

    operations = [
        migrations.CreateModel(
            name='InvoiceItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False,
                                           verbose_name='ID')),
                ('name', models.CharField(max_length=120)),
                ('description', models.CharField(max_length=1000)),
                ('quantity', models.IntegerField()),
                ('price', models.FloatField()),
                ('tax', models.FloatField(validators=[django.core.validators.MinValueValidator(0.0),
                                                      django.core.validators.MaxValueValidator(
                                                          1.0)])),
                ('invoice', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE,
                                              to='invoice.invoice')),
            ],
        ),
    ]
