# Generated by Django 4.1 on 2023-01-19 17:54

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('delivery', '0010_alter_deliverycart_user_address_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='deliverycart',
            name='public_uuid',
            field=models.UUIDField(auto_created=True, blank=True, default=uuid.UUID('323a3655-d9a7-4e71-b7b7-9f1d63530546')),
        ),
    ]
