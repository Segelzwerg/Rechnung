# Generated by Django 5.1.3 on 2024-11-25 23:05

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('invoice', '0016_rename_street_address_line_1_address_line_2_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='address',
            name='line_2',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
        migrations.AlterField(
            model_name='address',
            name='line_3',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
