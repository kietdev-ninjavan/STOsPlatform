# Generated by Django 5.1.1 on 2024-11-04 09:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sla_tool', '0002_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalshopeebacklog',
            name='shipper_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='historicaltiktokbacklog',
            name='shipper_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='shopeebacklog',
            name='shipper_date',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='tiktokbacklog',
            name='shipper_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
