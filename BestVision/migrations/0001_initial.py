# Generated by Django 5.1.6 on 2025-03-03 03:13

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Child',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('age', models.IntegerField()),
                ('admission_date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='Resource',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('type', models.CharField(choices=[('FOOD', 'Food'), ('CLOTHING', 'Clothing'), ('EDUCATION', 'Education'), ('MONEY', 'Money')], max_length=20)),
                ('quantity', models.FloatField()),
                ('unit', models.CharField(max_length=20)),
                ('cost_per_unit', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
        migrations.CreateModel(
            name='Requirement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity_per_child', models.FloatField()),
                ('frequency', models.CharField(choices=[('DAILY', 'Daily'), ('WEEKLY', 'Weekly'), ('MONTHLY', 'Monthly'), ('SEASONAL', 'Seasonal')], max_length=20)),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='BestVision.resource')),
            ],
        ),
        migrations.CreateModel(
            name='Allocation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.FloatField()),
                ('date_allocated', models.DateField(auto_now_add=True)),
                ('child', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='BestVision.child')),
                ('resource', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='BestVision.resource')),
            ],
        ),
    ]
