# Generated by Django 4.1 on 2022-10-19 20:45

import django.core.validators
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('in_place', '0012_dineinorder'),
    ]

    operations = [
        migrations.AddField(
            model_name='dineinorder',
            name='public_uuid',
            field=models.UUIDField(auto_created=True, default=uuid.uuid4, editable=False),
        ),
        migrations.AlterField(
            model_name='dineinorder',
            name='table_number',
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1)]),
        ),
    ]
