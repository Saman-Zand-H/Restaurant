# Generated by Django 4.1 on 2022-12-05 14:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurants', '0011_alter_order_timestamp'),
    ]

    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='timestamp',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
