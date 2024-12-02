# Generated by Django 5.1.3 on 2024-12-01 16:26

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('invoice', '0026_invoice_due_date_alter_invoice_currency_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='invoice',
            name='due_date_gte_date',
        ),
        migrations.AddConstraint(
            model_name='invoice',
            constraint=models.CheckConstraint(condition=models.Q(('date__gte', models.F('date'))),
                                              name='due_date_gte_date'),
        ),
    ]