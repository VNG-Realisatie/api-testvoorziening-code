# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-12-12 10:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testsession', '0024_auto_20181212_1041'),
    ]

    operations = [
        migrations.AlterField(
            model_name='session',
            name='exposed_api',
            field=models.CharField(blank=True, default=None, max_length=200, null=True),
        ),
    ]
