# Generated by Django 4.1 on 2022-11-24 21:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('in_place', '0016_delete_table'),
    ]

    operations = [
        migrations.AddField(
            model_name='staff',
            name='address',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
