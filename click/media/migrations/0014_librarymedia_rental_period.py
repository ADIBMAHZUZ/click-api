# Generated by Django 3.1.5 on 2022-07-15 08:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0013_auto_20220711_1706'),
    ]

    operations = [
        migrations.AddField(
            model_name='librarymedia',
            name='rental_period',
            field=models.CharField(blank=True, choices=[('12', '12'), ('24', '24'), ('36', '36'), ('48', '48')], max_length=10, null=True),
        ),
    ]
