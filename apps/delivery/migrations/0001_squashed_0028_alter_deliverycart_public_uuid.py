# Generated by Django 4.1 on 2023-02-01 23:57

import delivery.models
from django.conf import settings
import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import iranian_cities.fields
import uuid


class Migration(migrations.Migration):

    replaces = [('delivery', '0001_initial'), ('delivery', '0002_initial'), ('delivery', '0003_alter_deliverycartitem_public_uuid_and_more'), ('delivery', '0004_alter_deliverycartitem_item'), ('delivery', '0005_alter_useraddressinfo_options'), ('delivery', '0006_deliveryman_delete_delivery'), ('delivery', '0007_remove_deliverycart_paid'), ('delivery', '0008_deliverycart_date_created_and_more'), ('delivery', '0009_alter_deliverycart_unique_together_and_more'), ('delivery', '0010_alter_deliverycart_user_address_and_more'), ('delivery', '0011_deliverycart_public_uuid'), ('delivery', '0012_alter_deliverycart_public_uuid'), ('delivery', '0013_alter_deliverycart_public_uuid'), ('delivery', '0014_alter_deliverycart_public_uuid'), ('delivery', '0015_alter_deliverycart_public_uuid'), ('delivery', '0016_alter_deliverycart_public_uuid'), ('delivery', '0017_alter_deliverycart_public_uuid'), ('delivery', '0018_alter_deliverycart_public_uuid'), ('delivery', '0019_alter_deliverycart_public_uuid'), ('delivery', '0020_alter_deliverycart_public_uuid'), ('delivery', '0021_alter_deliverycart_public_uuid'), ('delivery', '0022_alter_deliverycart_public_uuid'), ('delivery', '0023_alter_deliverycart_public_uuid'), ('delivery', '0024_alter_deliverycart_public_uuid'), ('delivery', '0025_alter_deliverycart_public_uuid'), ('delivery', '0026_alter_deliverycart_public_uuid'), ('delivery', '0027_alter_deliverycart_public_uuid'), ('delivery', '0028_alter_deliverycart_public_uuid')]

    initial = True

    dependencies = [
        ('restaurants', '0005_remove_orderitem_cart_item_content_type_and_more'),
        ('restaurants', '0016_alter_orderitem_paid_price'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('azbankgateways', '0004_auto_20211115_1500'),
        ('restaurants', '0021_remove_order_user_remove_order_user_payment_and_more'),
        ('restaurants', '0001_initial'),
        ('iranian_cities', '0005_auto_20221004_0004'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserAddressInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public_uuid', models.UUIDField(auto_created=True, default=uuid.uuid4, editable=False, unique=True)),
                ('postal_code', models.CharField(max_length=30)),
                ('address', models.TextField()),
                ('location', django.contrib.gis.db.models.fields.PointField(srid=4326)),
                ('city', iranian_cities.fields.CityField(on_delete=django.db.models.deletion.CASCADE, to='iranian_cities.city')),
                ('province', iranian_cities.fields.ProvinceField(on_delete=django.db.models.deletion.CASCADE, to='iranian_cities.province')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_addresses', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name_plural': 'User Address Info',
            },
        ),
        migrations.CreateModel(
            name='Discount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('discount_code', models.CharField(auto_created=True, default=delivery.models.generate_discount_code, max_length=20, unique=True)),
                ('new_price', models.PositiveIntegerField()),
                ('date_created', models.DateTimeField(auto_now_add=True)),
                ('expiration_date', models.DateTimeField(blank=True, null=True)),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='item_discounts', to='restaurants.itemvariation')),
            ],
        ),
        migrations.CreateModel(
            name='DeliveryCart',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('discounts', models.ManyToManyField(related_name='discount_carts', to='delivery.discount')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='user_carts', to=settings.AUTH_USER_MODEL)),
                ('user_address', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='address_carts', to='delivery.useraddressinfo')),
                ('date_created', models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now)),
                ('date_submitted', models.DateTimeField(blank=True, null=True)),
                ('payment', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='payment_cart', to='azbankgateways.bank')),
                ('public_uuid', models.UUIDField(auto_created=True, blank=True, default=uuid.UUID('2e8d0d67-effb-49f0-85b3-7a0c1153b946'), unique=True)),
            ],
        ),
        migrations.CreateModel(
            name='DeliveryCartItem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('public_uuid', models.UUIDField(auto_created=True, default=uuid.uuid4, editable=False, unique=True)),
                ('count', models.PositiveIntegerField()),
                ('cart', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='cart_items', to='delivery.deliverycart')),
                ('discount', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='discount_items', to='delivery.discount')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='item_deliveries', to='restaurants.itemvariation')),
            ],
            options={
                'unique_together': {('item', 'cart')},
            },
        ),
        migrations.CreateModel(
            name='DeliveryMan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('vehicle_model', models.CharField(max_length=50)),
                ('vehicle_number', models.CharField(max_length=20)),
                ('unique_code', models.CharField(max_length=30)),
                ('restaurant', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='restaurnat_deliveries', to='restaurants.restaurant')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_deliveries', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]