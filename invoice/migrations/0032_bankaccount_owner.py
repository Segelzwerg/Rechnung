# Generated by Django 5.1.3 on 2024-12-06 11:12

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('invoice', '0031_invoice_final'),
    ]

    operations = [
        migrations.AddField(
            model_name='bankaccount',
            name='owner',
            field=models.CharField(default='', max_length=120),
        ),
    ]