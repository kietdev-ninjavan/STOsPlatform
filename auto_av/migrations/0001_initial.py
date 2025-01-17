# Generated by Django 5.1.1 on 2025-01-13 16:36

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
            name='OrderB2B',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('delete_at', models.DateTimeField(null=True)),
                ('tracking_id', models.CharField(max_length=255)),
                ('order_id', models.BigIntegerField(null=True)),
                ('status', models.CharField(choices=[('Completed', 'Completed'), ('Cancelled', 'Cancelled')], max_length=255, null=True)),
                ('granular_status', models.CharField(choices=[('En-route to Sorting Hub', 'En-route to Sorting Hub'), ('Arrived at Sorting Hub', 'Arrived at Sorting Hub'), ('Pending Reschedule', 'Pending Reschedule'), ('Pending Pickup', 'Pending Pickup'), ('Pending Pickup at Distribution Point', 'Pending Pickup at Distribution Point'), ('On Vehicle for Delivery', 'On Vehicle for Delivery'), ('On Hold', 'On Hold'), ('Transferred to 3PL', 'Transferred to 3PL'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled'), ('Returned to Sender', 'Returned to Sender')], max_length=255, null=True)),
                ('rts', models.BooleanField(default=False)),
                ('shipper_id', models.BigIntegerField(blank=True, null=True)),
                ('waypoint', models.BigIntegerField()),
                ('mps_id', models.BigIntegerField(blank=True, null=True)),
                ('mps_sequence_number', models.IntegerField(blank=True, null=True)),
                ('parcel_size', models.CharField(blank=True, max_length=255, null=True)),
                ('address', models.CharField(blank=True, max_length=255, null=True)),
                ('zone_id', models.IntegerField()),
                ('hub_id', models.IntegerField()),
                ('stage', models.CharField(choices=[('B2B-AV', 'B2B-AV'), ('B2B-LM-AV', 'B2B-LM-AV'), ('LM-AV', 'LM-AV'), ('In Queue', 'In Queue'), ('Not Verified', 'Not Verified')], default='Not Verified', max_length=255)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='HistoricalOrderB2B',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_date', models.DateTimeField(blank=True, editable=False)),
                ('updated_date', models.DateTimeField(blank=True, editable=False)),
                ('delete_at', models.DateTimeField(null=True)),
                ('tracking_id', models.CharField(max_length=255)),
                ('order_id', models.BigIntegerField(null=True)),
                ('status', models.CharField(choices=[('Completed', 'Completed'), ('Cancelled', 'Cancelled')], max_length=255, null=True)),
                ('granular_status', models.CharField(choices=[('En-route to Sorting Hub', 'En-route to Sorting Hub'), ('Arrived at Sorting Hub', 'Arrived at Sorting Hub'), ('Pending Reschedule', 'Pending Reschedule'), ('Pending Pickup', 'Pending Pickup'), ('Pending Pickup at Distribution Point', 'Pending Pickup at Distribution Point'), ('On Vehicle for Delivery', 'On Vehicle for Delivery'), ('On Hold', 'On Hold'), ('Transferred to 3PL', 'Transferred to 3PL'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled'), ('Returned to Sender', 'Returned to Sender')], max_length=255, null=True)),
                ('rts', models.BooleanField(default=False)),
                ('shipper_id', models.BigIntegerField(blank=True, null=True)),
                ('waypoint', models.BigIntegerField()),
                ('mps_id', models.BigIntegerField(blank=True, null=True)),
                ('mps_sequence_number', models.IntegerField(blank=True, null=True)),
                ('parcel_size', models.CharField(blank=True, max_length=255, null=True)),
                ('address', models.CharField(blank=True, max_length=255, null=True)),
                ('zone_id', models.IntegerField()),
                ('hub_id', models.IntegerField()),
                ('stage', models.CharField(choices=[('B2B-AV', 'B2B-AV'), ('B2B-LM-AV', 'B2B-LM-AV'), ('LM-AV', 'LM-AV'), ('In Queue', 'In Queue'), ('Not Verified', 'Not Verified')], default='Not Verified', max_length=255)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical order b2b',
                'verbose_name_plural': 'historical order b2bs',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
