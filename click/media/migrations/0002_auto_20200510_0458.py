# Generated by Django 3.0.4 on 2020-05-10 04:58

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='media',
            old_name='published_date',
            new_name='release_date',
        ),
    ]
