# Generated by Django 2.2a1 on 2019-04-25 08:50

from django.db import migrations, models
import django.db.models.deletion
import uuid


def create_uuid(apps, schema_editor):
    server = apps.get_model('servervalidation', 'ServerRun')
    for s in server.objects.all():
        s.uuid = uuid.uuid4()
        s.save()


class Migration(migrations.Migration):

    dependencies = [
        ('servervalidation', '0056_auto_20190411_1458'),
    ]

    operations = [
        migrations.AddField(
            model_name='serverrun',
            name='uuid',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.RunPython(create_uuid),
        migrations.AlterField(
            model_name='serverrun',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]
