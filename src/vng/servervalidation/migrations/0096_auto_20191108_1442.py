# Generated by Django 2.2.4 on 2019-11-08 13:42

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('servervalidation', '0095_auto_20191108_1436'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='api',
            options={'permissions': (('create_scenario_for_api', 'Create a test scenario for this API'),)},
        ),
    ]
