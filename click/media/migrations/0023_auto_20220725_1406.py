# Generated by Django 3.1.5 on 2022-07-25 07:06

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0022_auto_20220724_2157'),
    ]

    operations = [
        migrations.AlterField(
            model_name='librarymedia',
            name='expired_date',
            field=models.DateTimeField(default=datetime.datetime(2023, 7, 25, 7, 6, 39, 953574, tzinfo=utc)),
        ),
        migrations.AlterField(
            model_name='media',
            name='main_category',
            field=models.CharField(choices=[('Public', 'Public'), ('University/College', 'University/College'), ('Secondary School', 'Secondary School'), ('Primary School', 'Primary School'), ('Kindergarten', 'Kindergarten')], max_length=100, null=True),
        ),
    ]
