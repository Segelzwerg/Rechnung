# Generated by Django 5.1.3 on 2024-11-27 08:50

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('invoice', '0018_address_state'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='address',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                                       to='invoice.address'),
        ),
    ]
