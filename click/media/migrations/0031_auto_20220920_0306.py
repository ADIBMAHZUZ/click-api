# Generated by Django 3.0.4 on 2022-09-20 03:06

import datetime
from django.db import migrations, models
from django.utils.timezone import utc


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0030_auto_20220906_0653'),
    ]

    operations = [
        migrations.AlterField(
            model_name='librarymedia',
            name='expired_date',
            field=models.DateTimeField(default=datetime.datetime(2023, 9, 20, 3, 6, 27, 163599, tzinfo=utc)),
        ),
    ]
