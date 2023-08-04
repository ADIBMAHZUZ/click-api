# Generated by Django 3.1.5 on 2022-07-14 11:29

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('notification', '0008_quotation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='messagecontent',
            name='message_type',
            field=models.CharField(choices=[('request_storage', 'Request_storage'), ('request_delete_sub', 'Request_delete_sub'), ('confirm_delete_sub', 'Confirm_delete_sub'), ('request_delete_tea', 'Request_delete_tea'), ('confirm_delete_tea', 'Confirm_delete_tea'), ('request_media', 'Request_media'), ('confirm_storage', 'Confirm_storage'), ('confirm_media', 'Confirm_media'), ('confirm_upload', 'Confirm_upload'), ('send_quotation', 'Send_quotation')], max_length=20),
        ),
        migrations.AlterField(
            model_name='notificationreceiver',
            name='notification_type',
            field=models.CharField(choices=[('request_storage', 'Request_storage'), ('request_delete_sub', 'Request_delete_sub'), ('confirm_delete_sub', 'Confirm_delete_sub'), ('request_delete_tea', 'Request_delete_tea'), ('confirm_delete_tea', 'Confirm_delete_tea'), ('request_media', 'Request_media'), ('confirm_storage', 'Confirm_storage'), ('confirm_media', 'Confirm_media'), ('confirm_upload', 'Confirm_upload'), ('send_quotation', 'Send_quotation')], max_length=20),
        ),
        migrations.CreateModel(
            name='SendQuotation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('notification', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='send_quotation', to='notification.notificationreceiver')),
                ('quotation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_send_quotation', to='notification.quotation')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]