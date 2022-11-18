# Generated by Django 4.1 on 2022-11-13 19:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('restaurants', '0008_order_done'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='order_type',
            field=models.CharField(choices=[('d', 'delivery'), ('i', 'dine-in')], max_length=1),
        ),
    ]
