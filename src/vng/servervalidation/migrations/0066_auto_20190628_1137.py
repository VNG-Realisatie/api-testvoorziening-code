# Generated by Django 2.2.1 on 2019-06-28 09:37

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('servervalidation', '0065_merge_20190621_0817'),
    ]

    operations = [
        migrations.AddField(
            model_name='testscenariourl',
            name='placeholders',
            field=models.CharField(blank=True, default='https://www.example.com', max_length=100),
        ),
    ]
