# Generated by Django 4.1 on 2023-01-15 14:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('delivery', '0008_deliverycart_date_created_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='deliverycart',
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name='deliverycart',
            name='order',
        ),
    ]
