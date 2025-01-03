# Generated by Django 5.1.1 on 2024-11-28 16:23

import django.db.models.deletion
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('reco_ticket', '0002_alter_detectchangeaddress_options_and_more'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='TicketMissing',
            fields=[
                ('created_date', models.DateTimeField(auto_now_add=True)),
                ('updated_date', models.DateTimeField(auto_now=True)),
                ('delete_at', models.DateTimeField(null=True)),
                ('ticket_id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('tracking_id', models.CharField(max_length=255)),
                ('ticket_status', models.IntegerField(blank=True, choices=[(1, 'Pending'), (2, 'In Progress'), (3, 'Resolved'), (9, 'Pending Shipper'), (8, 'On Hold'), (13, 'Cancelled')], null=True)),
                ('ticket_type', models.IntegerField(blank=True, choices=[(1, 'DM'), (2, 'MI'), (3, 'SC'), (4, 'PE'), (5, 'SI'), (6, 'PH'), (7, 'SB')], null=True)),
                ('ticket_sub_type', models.IntegerField(blank=True, choices=[(1, 'IA'), (2, 'RZ'), (3, 'CO'), (4, 'CN'), (5, 'CR'), (6, 'NO'), (7, 'OO'), (8, 'PP'), (9, 'DP'), (10, 'RR'), (30, 'MA'), (34, 'DO'), (38, 'CQ'), (42, 'SQ'), (44, 'DZ'), (46, 'WR'), (48, 'RC'), (50, 'RG'), (52, 'NL'), (53, 'ND'), (54, 'MR'), (55, 'PL'), (56, 'SP'), (57, 'RO'), (58, 'RH'), (59, 'DE')], null=True)),
                ('hub_id', models.BigIntegerField(blank=True, null=True)),
                ('investigating_hub_id', models.BigIntegerField(blank=True, null=True)),
                ('order_id', models.BigIntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(blank=True, null=True)),
                ('shipper_id', models.BigIntegerField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('ws_last_scan', models.DateTimeField(blank=True, null=True)),
                ('ib_last_scan', models.DateTimeField(blank=True, null=True)),
                ('sm_last_scan', models.DateTimeField(blank=True, null=True)),
                ('need_resolve', models.BooleanField(default=False)),
                ('resolve_at', models.DateTimeField(blank=True, null=True)),
            ],
            options={
                'verbose_name': 'Ticket Missing',
                'verbose_name_plural': 'Tickets Missing',
            },
        ),
        migrations.CreateModel(
            name='HistoricalTicketMissing',
            fields=[
                ('created_date', models.DateTimeField(blank=True, editable=False)),
                ('updated_date', models.DateTimeField(blank=True, editable=False)),
                ('delete_at', models.DateTimeField(null=True)),
                ('ticket_id', models.BigIntegerField(db_index=True)),
                ('tracking_id', models.CharField(max_length=255)),
                ('ticket_status', models.IntegerField(blank=True, choices=[(1, 'Pending'), (2, 'In Progress'), (3, 'Resolved'), (9, 'Pending Shipper'), (8, 'On Hold'), (13, 'Cancelled')], null=True)),
                ('ticket_type', models.IntegerField(blank=True, choices=[(1, 'DM'), (2, 'MI'), (3, 'SC'), (4, 'PE'), (5, 'SI'), (6, 'PH'), (7, 'SB')], null=True)),
                ('ticket_sub_type', models.IntegerField(blank=True, choices=[(1, 'IA'), (2, 'RZ'), (3, 'CO'), (4, 'CN'), (5, 'CR'), (6, 'NO'), (7, 'OO'), (8, 'PP'), (9, 'DP'), (10, 'RR'), (30, 'MA'), (34, 'DO'), (38, 'CQ'), (42, 'SQ'), (44, 'DZ'), (46, 'WR'), (48, 'RC'), (50, 'RG'), (52, 'NL'), (53, 'ND'), (54, 'MR'), (55, 'PL'), (56, 'SP'), (57, 'RO'), (58, 'RH'), (59, 'DE')], null=True)),
                ('hub_id', models.BigIntegerField(blank=True, null=True)),
                ('investigating_hub_id', models.BigIntegerField(blank=True, null=True)),
                ('order_id', models.BigIntegerField(blank=True, null=True)),
                ('created_at', models.DateTimeField(blank=True, null=True)),
                ('shipper_id', models.BigIntegerField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, null=True)),
                ('ws_last_scan', models.DateTimeField(blank=True, null=True)),
                ('ib_last_scan', models.DateTimeField(blank=True, null=True)),
                ('sm_last_scan', models.DateTimeField(blank=True, null=True)),
                ('need_resolve', models.BooleanField(default=False)),
                ('resolve_at', models.DateTimeField(blank=True, null=True)),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'historical Ticket Missing',
                'verbose_name_plural': 'historical Tickets Missing',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
    ]
