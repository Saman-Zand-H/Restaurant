# Generated by Django 4.1 on 2022-10-13 16:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('in_place', '0009_remove_inplacecartitem_cart_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='staff',
            options={'permissions': (('delete_orders', 'is authorized to delete order records.'),)},
        ),
    ]
