# Generated by Django 3.0.4 on 2022-07-22 10:43

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0020_auto_20220722_1743'),
        ('notification', '0012_quotationdetail_rental_period'),
    ]

    operations = [
        migrations.CreateModel(
            name='RequestRenewMedia',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(default=0)),
                ('status', models.CharField(choices=[('approved', 'Approved'), ('pending', 'Pending'), ('rejected', 'Rejected')], max_length=20)),
                ('rental_period', models.CharField(blank=True, choices=[('12', '12'), ('24', '24'), ('36', '36'), ('48', '48')], max_length=10, null=True)),
                ('media', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_request_new_media', to='media.Media')),
                ('media_library', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='old_media_library', to='media.LibraryMedia')),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_request_new_media', to='notification.NotificationReceiver')),
            ],
            options={
                'db_table': 'notification_request_new_media',
            },
        ),
    ]
