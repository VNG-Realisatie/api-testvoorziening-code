# Generated by Django 2.2.13 on 2020-11-04 16:31

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('design_rules', '0013_auto_20201104_1642'),
    ]

    operations = [
        migrations.AlterField(
            model_name='designruletestoption',
            name='test_version',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='test_rules', to='design_rules.DesignRuleTestVersion'),
        ),
    ]
