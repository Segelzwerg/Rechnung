# Generated by Django 5.1.3 on 2024-11-22 10:22

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('invoice', '0010_alter_invoiceitem_price'),
    ]

    operations = [
        migrations.AddField(
            model_name='vendor',
            name='tax_id',
            field=models.CharField(blank=True, max_length=120, null=True),
        ),
    ]
