# Generated by Django 3.0.4 on 2022-10-06 04:43

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0024_auto_20220808_1603'),
    ]

    operations = [
        migrations.AddField(
            model_name='quotation',
            name='commission',
            field=models.FloatField(blank=True, null=True),
        ),
    ]
