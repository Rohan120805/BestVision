# Generated by Django 5.1.6 on 2025-03-11 05:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('BestVision', '0002_child_gender_resource_gender_specific_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='requirement',
            name='resource',
        ),
        migrations.AlterField(
            model_name='child',
            name='gender',
            field=models.CharField(choices=[('MALE', 'Male'), ('FEMALE', 'Female')], max_length=6),
        ),
        migrations.DeleteModel(
            name='Allocation',
        ),
        migrations.DeleteModel(
            name='Requirement',
        ),
        migrations.DeleteModel(
            name='Resource',
        ),
    ]
