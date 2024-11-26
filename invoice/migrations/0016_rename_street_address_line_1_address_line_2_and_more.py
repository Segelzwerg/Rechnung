# Generated by Django 5.1.3 on 2024-11-25 22:59

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('invoice', '0015_alter_bankaccount_iban'),
    ]

    operations = [
        migrations.RenameField(
            model_name='address',
            old_name='street',
            new_name='line_1',
        ),
        migrations.AddField(
            model_name='address',
            name='line_2',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='address',
            name='line_3',
            field=models.CharField(default='', max_length=200),
            preserve_default=False,
        ),
    ]