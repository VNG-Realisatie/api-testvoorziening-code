# -*- coding: utf-8 -*-
# Generated by Django 1.11.16 on 2018-12-20 19:07
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('testsession', '0046_auto_20181220_1818'),
    ]

    operations = [
        migrations.AlterField(
            model_name='session',
            name='session_type',
            field=models.ForeignKey(default=1, on_delete=django.db.models.deletion.CASCADE, to='testsession.SessionType'),
            preserve_default=False,
        ),
    ]