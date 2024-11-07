# Generated by Django 5.1.1 on 2024-11-07 10:52

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
            name='PickupJob',
            fields=[
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('delete_at', models.DateTimeField(null=True)),
                ('job_id', models.IntegerField(primary_key=True, serialize=False)),
                ('shipper_id', models.BigIntegerField(null=True)),
                ('shipper_name', models.CharField(max_length=255, null=True)),
                ('contact', models.CharField(max_length=20, null=True)),
                ('waypoint_id', models.BigIntegerField(null=True)),
                ('status', models.CharField(choices=[('ready-for-routing', 'Ready for Routing'), ('routed', 'Routed'), ('in-progress', 'In Progress'), ('cancelled', 'Cancelled'), ('completed', 'Completed'), ('failed', 'Failed'), ('no-pop', 'No POP')], max_length=20, null=True)),
                ('driver_id', models.IntegerField(null=True)),
                ('pickup_schedule_date', models.DateField(null=True)),
                ('shipper_address', models.CharField(max_length=255, null=True)),
                ('call_center_status', models.CharField(max_length=255, null=True)),
                ('call_center_sent_time', models.DateTimeField(null=True)),
            ],
            options={
                'verbose_name': 'Fail Pickup Job',
                'verbose_name_plural': 'Fail Pickup Jobs',
            },
        ),
        migrations.CreateModel(
            name='Route',
            fields=[
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('delete_at', models.DateTimeField(null=True)),
                ('route_id', models.AutoField(primary_key=True, serialize=False)),
                ('archived', models.BooleanField(default=False)),
                ('driver_id', models.IntegerField(null=True)),
            ],
            options={
                'verbose_name': 'Fail Pickup Route',
                'verbose_name_plural': 'Fail Pickup Routes',
            },
        ),
        migrations.CreateModel(
            name='HistoricalRoute',
            fields=[
                ('created_date', models.DateTimeField(blank=True, editable=False)),
                ('updated_date', models.DateTimeField(blank=True, editable=False)),
                ('delete_at', models.DateTimeField(null=True)),
                ('route_id', models.IntegerField(blank=True, db_index=True)),
                ('archived', models.BooleanField(default=False)),
                ('driver_id', models.IntegerField(null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical Fail Pickup Route',
                'verbose_name_plural': 'historical Fail Pickup Routes',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalPickupJobOrder',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_date', models.DateTimeField(blank=True, editable=False)),
                ('updated_date', models.DateTimeField(blank=True, editable=False)),
                ('delete_at', models.DateTimeField(null=True)),
                ('order_id', models.IntegerField()),
                ('tracking_id', models.CharField(max_length=255, null=True)),
                ('parcel_size', models.CharField(max_length=255, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('job_id', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='fail_pickup.pickupjob')),
            ],
            options={
                'verbose_name': 'historical Fail Pickup Job Order',
                'verbose_name_plural': 'historical Fail Pickup Job Orders',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='PickupJobOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('delete_at', models.DateTimeField(null=True)),
                ('order_id', models.IntegerField()),
                ('tracking_id', models.CharField(max_length=255, null=True)),
                ('parcel_size', models.CharField(max_length=255, null=True)),
                ('job_id', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='packets', to='fail_pickup.pickupjob')),
            ],
            options={
                'verbose_name': 'Fail Pickup Job Order',
                'verbose_name_plural': 'Fail Pickup Job Orders',
            },
        ),
        migrations.AddField(
            model_name='pickupjob',
            name='route',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='pickup_jobs', to='fail_pickup.route'),
        ),
        migrations.CreateModel(
            name='HistoricalPickupJob',
            fields=[
                ('created_date', models.DateTimeField(blank=True, editable=False)),
                ('updated_date', models.DateTimeField(blank=True, editable=False)),
                ('delete_at', models.DateTimeField(null=True)),
                ('job_id', models.IntegerField(db_index=True)),
                ('shipper_id', models.BigIntegerField(null=True)),
                ('shipper_name', models.CharField(max_length=255, null=True)),
                ('contact', models.CharField(max_length=20, null=True)),
                ('waypoint_id', models.BigIntegerField(null=True)),
                ('status', models.CharField(choices=[('ready-for-routing', 'Ready for Routing'), ('routed', 'Routed'), ('in-progress', 'In Progress'), ('cancelled', 'Cancelled'), ('completed', 'Completed'), ('failed', 'Failed'), ('no-pop', 'No POP')], max_length=20, null=True)),
                ('driver_id', models.IntegerField(null=True)),
                ('pickup_schedule_date', models.DateField(null=True)),
                ('shipper_address', models.CharField(max_length=255, null=True)),
                ('call_center_status', models.CharField(max_length=255, null=True)),
                ('call_center_sent_time', models.DateTimeField(null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('route', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='fail_pickup.route')),
            ],
            options={
                'verbose_name': 'historical Fail Pickup Job',
                'verbose_name_plural': 'historical Fail Pickup Jobs',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
