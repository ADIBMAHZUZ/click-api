# Generated by Django 3.0.4 on 2020-06-19 11:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='category',
            name='category_type',
        ),
    ]
