# Generated by Django 5.1.4 on 2025-01-08 19:47

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('invoice', '0038_alter_bankaccount_bic_alter_bankaccount_iban_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='Discount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('amount', models.DecimalField(decimal_places=2, max_digits=20, verbose_name='discount')),
            ],
        ),
        migrations.CreateModel(
            name='FlatDiscount',
            fields=[
                ('discount_ptr',
                 models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True,
                                      primary_key=True, serialize=False, to='invoice.discount')),
            ],
            bases=('invoice.discount',),
        ),
        migrations.CreateModel(
            name='RelativeDiscount',
            fields=[
                ('discount_ptr',
                 models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True,
                                      primary_key=True, serialize=False, to='invoice.discount')),
            ],
            bases=('invoice.discount',),
        ),
        migrations.AddField(
            model_name='invoice',
            name='discount',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE,
                                    to='invoice.discount', verbose_name='discount'),
        ),
    ]
