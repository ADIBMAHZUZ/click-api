# Generated by Django 3.1.5 on 2022-07-17 15:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0009_auto_20220714_1829'),
    ]

    operations = [
        migrations.AddField(
            model_name='requestmedia',
            name='rental_period',
            field=models.CharField(blank=True, choices=[('12', '12'), ('24', '24'), ('36', '36'), ('48', '48')], max_length=10, null=True),
        ),
    ]
