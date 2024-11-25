# Generated by Django 5.1.1 on 2024-10-31 07:45

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
            name='Hub',
            fields=[
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('delete_at', models.DateTimeField(null=True)),
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=255)),
                ('country', models.CharField(blank=True, max_length=255, null=True)),
                ('city', models.CharField(blank=True, max_length=255, null=True)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('region', models.CharField(blank=True, max_length=255, null=True)),
                ('area', models.CharField(blank=True, max_length=255, null=True)),
                ('active', models.BooleanField(default=True)),
                ('short_name', models.CharField(blank=True, max_length=255, null=True)),
                ('sort_hub', models.BooleanField(default=False)),
                ('facility_type', models.CharField(blank=True, max_length=255, null=True)),
                ('opv2_created_at', models.DateTimeField(auto_now_add=True)),
                ('opv2_updated_at', models.DateTimeField(auto_now=True)),
                ('virtual_hub', models.BooleanField(default=False)),
                ('parent_hub', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'verbose_name': 'Hub',
                'verbose_name_plural': 'Hubs',
            },
        ),
        migrations.CreateModel(
            name='Zone',
            fields=[
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('delete_at', models.DateTimeField(null=True)),
                ('id', models.IntegerField(primary_key=True, serialize=False)),
                ('legacy_zone_id', models.IntegerField(blank=True, null=True)),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('type', models.CharField(blank=True, max_length=255, null=True)),
                ('hub_id', models.IntegerField(blank=True, null=True)),
                ('short_name', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Zone',
                'verbose_name_plural': 'Zones',
            },
        ),
        migrations.CreateModel(
            name='HistoricalHub',
            fields=[
                ('created_date', models.DateTimeField(blank=True, editable=False)),
                ('updated_date', models.DateTimeField(blank=True, editable=False)),
                ('delete_at', models.DateTimeField(null=True)),
                ('id', models.IntegerField(db_index=True)),
                ('name', models.CharField(max_length=255)),
                ('country', models.CharField(blank=True, max_length=255, null=True)),
                ('city', models.CharField(blank=True, max_length=255, null=True)),
                ('latitude', models.FloatField()),
                ('longitude', models.FloatField()),
                ('region', models.CharField(blank=True, max_length=255, null=True)),
                ('area', models.CharField(blank=True, max_length=255, null=True)),
                ('active', models.BooleanField(default=True)),
                ('short_name', models.CharField(blank=True, max_length=255, null=True)),
                ('sort_hub', models.BooleanField(default=False)),
                ('facility_type', models.CharField(blank=True, max_length=255, null=True)),
                ('opv2_created_at', models.DateTimeField(blank=True, editable=False)),
                ('opv2_updated_at', models.DateTimeField(blank=True, editable=False)),
                ('virtual_hub', models.BooleanField(default=False)),
                ('parent_hub', models.CharField(blank=True, max_length=255, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical Hub',
                'verbose_name_plural': 'historical Hubs',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalZone',
            fields=[
                ('created_date', models.DateTimeField(blank=True, editable=False)),
                ('updated_date', models.DateTimeField(blank=True, editable=False)),
                ('delete_at', models.DateTimeField(null=True)),
                ('id', models.IntegerField(db_index=True)),
                ('legacy_zone_id', models.IntegerField(blank=True, null=True)),
                ('name', models.CharField(blank=True, max_length=255, null=True)),
                ('type', models.CharField(blank=True, max_length=255, null=True)),
                ('hub_id', models.IntegerField(blank=True, null=True)),
                ('short_name', models.CharField(blank=True, max_length=255, null=True)),
                ('description', models.TextField(blank=True, null=True)),
                ('latitude', models.FloatField(blank=True, null=True)),
                ('longitude', models.FloatField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical Zone',
                'verbose_name_plural': 'historical Zones',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
