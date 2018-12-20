# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-12-17 11:36
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion

def forwards_func(apps, schema_editor):
    VNGEndpoint = apps.get_model("testsession", "VNGEndpoint")
    SessionType = apps.get_model("testsession", "SessionType")
    if not VNGEndpoint.objects.filter(id=1):
        VNGEndpoint.objects.create(name='Example', url='https://vng.nl', session_type=SessionType.objects.first())

def reverse_func(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    
    dependencies = [
        ('testsession', '0033_auto_20181217_1227'),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_func),
        migrations.AlterField(
            model_name='scenariocase',
            name='vng_endpoint',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='testsession.VNGEndpoint'),
        ),
    ]
