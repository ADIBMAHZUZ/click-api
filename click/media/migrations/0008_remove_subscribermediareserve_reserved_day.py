# Generated by Django 3.0.4 on 2020-07-07 08:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0007_delete_librarymediatransaction'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subscribermediareserve',
            name='reserved_day',
        ),
    ]
