# Generated by Django 4.1 on 2022-11-25 18:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('in_place', '0017_staff_address'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='staff',
            options={'permissions': [('delete_orders', 'is authorized to delete order records.'), ('read_salaries', "is authorized to read other staff's salaries"), ('read_staff', 'has access to details of the staff'), ('mod_staff', 'can add, modify, or delete members for the staff')]},
        ),
    ]