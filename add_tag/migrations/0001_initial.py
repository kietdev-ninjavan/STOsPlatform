# Generated by Django 5.1.1 on 2024-11-15 08:21

import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PriorB2B',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('delete_at', models.DateTimeField(null=True)),
                ('order_id', models.BigIntegerField()),
                ('tracking_id', models.CharField(max_length=255)),
                ('granular_status', models.CharField(max_length=255)),
                ('shipper_id', models.BigIntegerField()),
                ('shipper_name', models.CharField(max_length=255)),
                ('curr_zone_name', models.CharField(max_length=255)),
                ('creation_datetime', models.DateTimeField()),
                ('pickup_datetime', models.DateTimeField()),
                ('pickup_hub_name', models.CharField(max_length=255)),
                ('delivery_hub_name', models.CharField(max_length=255)),
                ('route', models.CharField(max_length=255)),
                ('date_to_prior', models.DateField()),
            ],
            options={
                'verbose_name': 'Prior Tag B2B',
                'verbose_name_plural': 'Prior Tag B2B',
            },
        ),
        migrations.CreateModel(
            name='HistoricalPriorB2B',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_date', models.DateTimeField(blank=True, editable=False)),
                ('updated_date', models.DateTimeField(blank=True, editable=False)),
                ('delete_at', models.DateTimeField(null=True)),
                ('order_id', models.BigIntegerField()),
                ('tracking_id', models.CharField(max_length=255)),
                ('granular_status', models.CharField(max_length=255)),
                ('shipper_id', models.BigIntegerField()),
                ('shipper_name', models.CharField(max_length=255)),
                ('curr_zone_name', models.CharField(max_length=255)),
                ('creation_datetime', models.DateTimeField()),
                ('pickup_datetime', models.DateTimeField()),
                ('pickup_hub_name', models.CharField(max_length=255)),
                ('delivery_hub_name', models.CharField(max_length=255)),
                ('route', models.CharField(max_length=255)),
                ('date_to_prior', models.DateField()),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical Prior Tag B2B',
                'verbose_name_plural': 'historical Prior Tag B2B',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]