# Generated by Django 3.0.4 on 2022-07-05 09:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0006_auto_20220704_1701'),
    ]

    operations = [
        migrations.AlterField(
            model_name='requestdeletesubscriber',
            name='subscriber',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
        migrations.AlterField(
            model_name='requestdeleteteacher',
            name='teacher',
            field=models.CharField(blank=True, max_length=20, null=True),
        ),
    ]