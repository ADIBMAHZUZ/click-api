# Generated by Django 3.1.5 on 2022-08-05 06:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0018_expiredmedia_media_library'),
    ]

    operations = [
        migrations.AddField(
            model_name='sendquotation',
            name='status',
            field=models.CharField(choices=[('approved', 'Approved'), ('pending', 'Pending'), ('rejected', 'Rejected')], default='pending', max_length=20),
        ),
    ]
