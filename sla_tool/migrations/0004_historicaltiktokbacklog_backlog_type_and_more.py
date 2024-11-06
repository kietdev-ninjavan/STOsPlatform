# Generated by Django 5.1.1 on 2024-11-06 03:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sla_tool', '0003_historicalshopeebacklog_shipper_date_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicaltiktokbacklog',
            name='backlog_type',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='tiktokbacklog',
            name='backlog_type',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
