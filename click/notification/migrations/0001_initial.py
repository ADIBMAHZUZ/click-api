# Generated by Django 3.0.4 on 2020-06-30 11:24

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('media', '0007_delete_librarymediatransaction'),
    ]

    operations = [
        migrations.CreateModel(
            name='MessageContent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('message_type', models.CharField(choices=[('request_storage', 'Request_storage'), ('request_media', 'Request_media'), ('confirm_storage', 'Confirm_storage'), ('confirm_media', 'Confirm_media'), ('confirm_upload', 'Confirm_upload')], max_length=20)),
                ('description', models.CharField(max_length=255, null=True)),
                ('message_to_producer', models.CharField(max_length=255, null=True)),
                ('message_to_receiver', models.CharField(max_length=255, null=True)),
                ('message_to_producer_malay', models.CharField(max_length=255, null=True)),
                ('message_to_receiver_malay', models.CharField(max_length=255, null=True)),
            ],
            options={
                'db_table': 'notification_message',
            },
        ),
        migrations.CreateModel(
            name='NotificationProducer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='producer', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'notification_producer',
            },
        ),
        migrations.CreateModel(
            name='NotificationReceiver',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('notification_type', models.CharField(choices=[('request_storage', 'Request_storage'), ('request_media', 'Request_media'), ('confirm_storage', 'Confirm_storage'), ('confirm_media', 'Confirm_media'), ('confirm_upload', 'Confirm_upload')], max_length=20)),
                ('is_active', models.BooleanField(default=False)),
                ('message', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receivers', to='notification.MessageContent')),
                ('producer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='noti_receiver', to='notification.NotificationProducer')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receiver', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'notification_receiver',
            },
        ),
        migrations.CreateModel(
            name='RequestStorage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_upgrade', models.IntegerField(default=1)),
                ('status', models.CharField(choices=[('approve', 'Approve'), ('waiting', 'Waiting'), ('reject', 'Reject')], max_length=20)),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='request_storage', to='notification.NotificationReceiver')),
            ],
            options={
                'db_table': 'notification_request_storage',
            },
        ),
        migrations.CreateModel(
            name='RequestMedia',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.IntegerField(default=0)),
                ('status', models.CharField(choices=[('approve', 'Approve'), ('waiting', 'Waiting'), ('reject', 'Reject')], max_length=20)),
                ('media', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='request_media', to='media.Media')),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='request_media', to='notification.NotificationReceiver')),
            ],
            options={
                'db_table': 'notification_request_media',
            },
        ),
        migrations.CreateModel(
            name='ConfirmUpload',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('upload_type', models.CharField(choices=[('media', 'Media'), ('learning_material', 'Learning_material'), ('teacher_notes', 'Teacher_notes'), ('student_content', 'Student_content'), ('school_news_board', 'School_news_board'), ('school_history', 'School_history')], max_length=50)),
                ('name', models.CharField(max_length=255, null=True)),
                ('media_type', models.CharField(max_length=255, null=True)),
                ('receiver', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='confirm_upload', to='notification.NotificationReceiver')),
            ],
            options={
                'db_table': 'notification_confirm_upload',
            },
        ),
        migrations.CreateModel(
            name='ConfirmStorage',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('approve', 'Approve'), ('waiting', 'Waiting'), ('reject', 'Reject')], max_length=20)),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='confirm_storage', to='notification.NotificationReceiver')),
                ('request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='confirm_storages', to='notification.RequestStorage')),
            ],
            options={
                'db_table': 'notification_confirm_storage',
            },
        ),
        migrations.CreateModel(
            name='ConfirmMedia',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status', models.CharField(choices=[('approve', 'Approve'), ('waiting', 'Waiting'), ('reject', 'Reject')], max_length=20)),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='confirm_media', to='notification.NotificationReceiver')),
                ('request', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='confirm_medias', to='notification.RequestMedia')),
            ],
            options={
                'db_table': 'notification_confirm_media',
            },
        ),
    ]