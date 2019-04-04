# Generated by Django 2.2a1 on 2019-02-19 10:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('testsession', '0057_exposedurl_docker_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='vngendpoint',
            name='url',
            field=models.URLField(blank=True, default=None, null=True),
        ),
        migrations.RemoveField(
            model_name='vngendpoint',
            name='test_file',
        ),
    ]