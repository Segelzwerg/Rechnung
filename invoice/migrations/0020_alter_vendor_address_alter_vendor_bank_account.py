# Generated by Django 5.1.3 on 2024-11-27 11:41

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('invoice', '0019_alter_customer_address'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vendor',
            name='address',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE,
                                       to='invoice.address'),
        ),
        migrations.AlterField(
            model_name='vendor',
            name='bank_account',
            field=models.OneToOneField(blank=True, null=True,
                                       on_delete=django.db.models.deletion.CASCADE,
                                       to='invoice.bankaccount'),
        ),
    ]
