# Generated by Django 4.1 on 2022-12-24 01:00

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('in_place', '0021_alter_dineinorder_table_number'),
    ]

    operations = [
        migrations.AlterField(
            model_name='dineinorder',
            name='timestamp',
            field=models.DateTimeField(default=datetime.datetime(2022, 12, 24, 1, 0, 19, 775218, tzinfo=datetime.timezone.utc)),
        ),
    ]