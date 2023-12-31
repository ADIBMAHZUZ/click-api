# Generated by Django 3.0.4 on 2022-07-22 07:02

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    dependencies = [
        ('media', '0017_auto_20220722_1402'),
        ('notification', '0010_requestmedia_rental_period'),
    ]

    operations = [
        migrations.AddField(
            model_name='quotation',
            name='total',
            field=models.FloatField(default=0),
        ),
        migrations.CreateModel(
            name='QuotationDetail',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('price', models.FloatField(blank=True, null=True)),
                ('quantity', models.IntegerField(default=0)),
                ('media', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='quotation_media', to='media.Media')),
                ('quotation', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_quotation_detail', to='notification.Quotation')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
