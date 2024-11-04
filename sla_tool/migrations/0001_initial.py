# Generated by Django 5.1.1 on 2024-10-28 11:11

import simple_history.models
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ExtendSLATracking',
            fields=[
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('delete_at', models.DateTimeField(null=True)),
                ('tracking_id', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('extend_days', models.IntegerField(blank=True, null=True)),
                ('sla_date', models.DateField(blank=True, null=True)),
                ('breach_sla_date', models.DateField(blank=True, null=True)),
                ('first_sla_expectation', models.DateField(blank=True, null=True)),
                ('breach_sla_expectation', models.DateField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Extend SLA Tracking ID',
                'verbose_name_plural': 'Extend SLA Tracking IDs',
            },
        ),
        migrations.CreateModel(
            name='HistoricalBreachSLACall',
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
                ('shipper_group', models.CharField(blank=True, max_length=255, null=True)),
                ('shipper_name', models.CharField(blank=True, max_length=255, null=True)),
                ('num_of_attempts', models.IntegerField(default=False)),
                ('to_name', models.CharField(blank=True, max_length=255, null=True)),
                ('to_contact', models.CharField(blank=True, max_length=255, null=True)),
                ('to_address1', models.TextField(blank=True, null=True)),
                ('cod', models.FloatField(blank=True, null=True)),
                ('item_description', models.TextField(blank=True, null=True)),
                ('hub_id', models.IntegerField(blank=True, null=True)),
                ('hub_name', models.CharField(blank=True, max_length=255, null=True)),
                ('hub_region', models.CharField(blank=True, max_length=255, null=True)),
                ('last_fail_attempt', models.CharField(blank=True, max_length=255, null=True)),
                ('gform_url', models.URLField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('call_type', models.CharField(blank=True, max_length=255, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical Breach SLA Call',
                'verbose_name_plural': 'historical Breach SLA Calls',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalExtendSLATracking',
            fields=[
                ('created_date', models.DateTimeField(blank=True, editable=False)),
                ('updated_date', models.DateTimeField(blank=True, editable=False)),
                ('delete_at', models.DateTimeField(null=True)),
                ('tracking_id', models.CharField(db_index=True, max_length=255)),
                ('extend_days', models.IntegerField(blank=True, null=True)),
                ('sla_date', models.DateField(blank=True, null=True)),
                ('breach_sla_date', models.DateField(blank=True, null=True)),
                ('first_sla_expectation', models.DateField(blank=True, null=True)),
                ('breach_sla_expectation', models.DateField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical Extend SLA Tracking ID',
                'verbose_name_plural': 'historical Extend SLA Tracking IDs',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalRecordSLACall',
            fields=[
                ('created_date', models.DateTimeField(blank=True, editable=False)),
                ('updated_date', models.DateTimeField(blank=True, editable=False)),
                ('delete_at', models.DateTimeField(null=True)),
                ('tracking_id', models.CharField(db_index=True, max_length=255)),
                ('collect_date', models.DateField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical record sla call',
                'verbose_name_plural': 'historical record sla calls',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalShopeeBacklog',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('created_date', models.DateTimeField(blank=True, editable=False)),
                ('updated_date', models.DateTimeField(blank=True, editable=False)),
                ('delete_at', models.DateTimeField(null=True)),
                ('order_id', models.BigIntegerField(null=True)),
                ('status', models.CharField(choices=[('Completed', 'Completed'), ('Cancelled', 'Cancelled')], max_length=255, null=True)),
                ('granular_status', models.CharField(choices=[('En-route to Sorting Hub', 'En-route to Sorting Hub'), ('Arrived at Sorting Hub', 'Arrived at Sorting Hub'), ('Pending Reschedule', 'Pending Reschedule'), ('Pending Pickup', 'Pending Pickup'), ('Pending Pickup at Distribution Point', 'Pending Pickup at Distribution Point'), ('On Vehicle for Delivery', 'On Vehicle for Delivery'), ('On Hold', 'On Hold'), ('Transferred to 3PL', 'Transferred to 3PL'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled'), ('Returned to Sender', 'Returned to Sender')], max_length=255, null=True)),
                ('rts', models.BooleanField(default=False)),
                ('tracking_id', models.CharField(max_length=255)),
                ('backlog_type', models.CharField(blank=True, max_length=255, null=True)),
                ('order_sn', models.CharField(max_length=255)),
                ('return_sn', models.CharField(blank=True, max_length=255, null=True)),
                ('return_id', models.BigIntegerField(blank=True, null=True)),
                ('consignment_no', models.CharField(blank=True, max_length=255, null=True)),
                ('aging_from_lost_threshold', models.IntegerField(blank=True, null=True)),
                ('create_time', models.DateTimeField(blank=True, null=True)),
                ('pickup_done_time', models.DateTimeField(blank=True, null=True)),
                ('extend_days', models.IntegerField(blank=True, null=True)),
                ('extended_date', models.DateField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical Shopee Backlog',
                'verbose_name_plural': 'historical Shopee Backlogs',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalTiktokBacklog',
            fields=[
                ('created_date', models.DateTimeField(blank=True, editable=False)),
                ('updated_date', models.DateTimeField(blank=True, editable=False)),
                ('delete_at', models.DateTimeField(null=True)),
                ('order_id', models.BigIntegerField(null=True)),
                ('status', models.CharField(choices=[('Completed', 'Completed'), ('Cancelled', 'Cancelled')], max_length=255, null=True)),
                ('granular_status', models.CharField(choices=[('En-route to Sorting Hub', 'En-route to Sorting Hub'), ('Arrived at Sorting Hub', 'Arrived at Sorting Hub'), ('Pending Reschedule', 'Pending Reschedule'), ('Pending Pickup', 'Pending Pickup'), ('Pending Pickup at Distribution Point', 'Pending Pickup at Distribution Point'), ('On Vehicle for Delivery', 'On Vehicle for Delivery'), ('On Hold', 'On Hold'), ('Transferred to 3PL', 'Transferred to 3PL'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled'), ('Returned to Sender', 'Returned to Sender')], max_length=255, null=True)),
                ('rts', models.BooleanField(default=False)),
                ('ticket_no', models.BigIntegerField(blank=True, null=True)),
                ('tracking_id', models.CharField(db_index=True, max_length=255)),
                ('date', models.DateField(blank=True, null=True)),
                ('extend_days', models.IntegerField(blank=True, default=2, null=True)),
                ('extended_date', models.DateField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
            ],
            options={
                'verbose_name': 'historical Tiktok Backlog',
                'verbose_name_plural': 'historical Tiktok Backlogs',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='RecordSLACall',
            fields=[
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('delete_at', models.DateTimeField(null=True)),
                ('tracking_id', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('collect_date', models.DateField(blank=True, null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ShopeeBacklog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('delete_at', models.DateTimeField(null=True)),
                ('order_id', models.BigIntegerField(null=True)),
                ('status', models.CharField(choices=[('Completed', 'Completed'), ('Cancelled', 'Cancelled')], max_length=255, null=True)),
                ('granular_status', models.CharField(choices=[('En-route to Sorting Hub', 'En-route to Sorting Hub'), ('Arrived at Sorting Hub', 'Arrived at Sorting Hub'), ('Pending Reschedule', 'Pending Reschedule'), ('Pending Pickup', 'Pending Pickup'), ('Pending Pickup at Distribution Point', 'Pending Pickup at Distribution Point'), ('On Vehicle for Delivery', 'On Vehicle for Delivery'), ('On Hold', 'On Hold'), ('Transferred to 3PL', 'Transferred to 3PL'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled'), ('Returned to Sender', 'Returned to Sender')], max_length=255, null=True)),
                ('rts', models.BooleanField(default=False)),
                ('tracking_id', models.CharField(max_length=255)),
                ('backlog_type', models.CharField(blank=True, max_length=255, null=True)),
                ('order_sn', models.CharField(max_length=255)),
                ('return_sn', models.CharField(blank=True, max_length=255, null=True)),
                ('return_id', models.BigIntegerField(blank=True, null=True)),
                ('consignment_no', models.CharField(blank=True, max_length=255, null=True)),
                ('aging_from_lost_threshold', models.IntegerField(blank=True, null=True)),
                ('create_time', models.DateTimeField(blank=True, null=True)),
                ('pickup_done_time', models.DateTimeField(blank=True, null=True)),
                ('extend_days', models.IntegerField(blank=True, null=True)),
                ('extended_date', models.DateField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Shopee Backlog',
                'verbose_name_plural': 'Shopee Backlogs',
            },
        ),
        migrations.CreateModel(
            name='TiktokBacklog',
            fields=[
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('delete_at', models.DateTimeField(null=True)),
                ('order_id', models.BigIntegerField(null=True)),
                ('status', models.CharField(choices=[('Completed', 'Completed'), ('Cancelled', 'Cancelled')], max_length=255, null=True)),
                ('granular_status', models.CharField(choices=[('En-route to Sorting Hub', 'En-route to Sorting Hub'), ('Arrived at Sorting Hub', 'Arrived at Sorting Hub'), ('Pending Reschedule', 'Pending Reschedule'), ('Pending Pickup', 'Pending Pickup'), ('Pending Pickup at Distribution Point', 'Pending Pickup at Distribution Point'), ('On Vehicle for Delivery', 'On Vehicle for Delivery'), ('On Hold', 'On Hold'), ('Transferred to 3PL', 'Transferred to 3PL'), ('Completed', 'Completed'), ('Cancelled', 'Cancelled'), ('Returned to Sender', 'Returned to Sender')], max_length=255, null=True)),
                ('rts', models.BooleanField(default=False)),
                ('ticket_no', models.BigIntegerField(blank=True, null=True)),
                ('tracking_id', models.CharField(max_length=255, primary_key=True, serialize=False)),
                ('date', models.DateField(blank=True, null=True)),
                ('extend_days', models.IntegerField(blank=True, default=2, null=True)),
                ('extended_date', models.DateField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Tiktok Backlog',
                'verbose_name_plural': 'Tiktok Backlogs',
            },
        ),
        migrations.CreateModel(
            name='BreachSLACall',
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
                ('shipper_group', models.CharField(blank=True, max_length=255, null=True)),
                ('shipper_name', models.CharField(blank=True, max_length=255, null=True)),
                ('num_of_attempts', models.IntegerField(default=False)),
                ('to_name', models.CharField(blank=True, max_length=255, null=True)),
                ('to_contact', models.CharField(blank=True, max_length=255, null=True)),
                ('to_address1', models.TextField(blank=True, null=True)),
                ('cod', models.FloatField(blank=True, null=True)),
                ('item_description', models.TextField(blank=True, null=True)),
                ('hub_id', models.IntegerField(blank=True, null=True)),
                ('hub_name', models.CharField(blank=True, max_length=255, null=True)),
                ('hub_region', models.CharField(blank=True, max_length=255, null=True)),
                ('last_fail_attempt', models.CharField(blank=True, max_length=255, null=True)),
                ('gform_url', models.URLField(blank=True, null=True)),
                ('updated_at', models.DateTimeField(blank=True, null=True)),
                ('call_type', models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                'verbose_name': 'Breach SLA Call',
                'verbose_name_plural': 'Breach SLA Calls',
                'constraints': [models.UniqueConstraint(fields=('tracking_id', 'updated_at'), name='unique_breach_tracking_update')],
            },
        ),
    ]