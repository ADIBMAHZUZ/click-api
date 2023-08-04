# Generated by Django 3.1.5 on 2022-08-01 09:30

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0026_auto_20220801_1048'),
    ]

    operations = [
        migrations.AlterField(
            model_name='librarymedia',
            name='expired_date',
            field=models.DateTimeField(default=datetime.datetime(2023, 8, 1, 9, 30, 5, 621180, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='media',
            name='main_category',
            field=models.CharField(choices=[('Public', 'Public'), ('University/College', 'University/College'), ('Secondary School', 'Secondary School'), ('Primary School', 'Primary School'), ('Kindergarten', 'Kindergarten')], default='Public', max_length=100, null=True),
        ),
    ]