# Generated by Django 3.0.4 on 2020-07-08 09:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('master_data', '0002_remove_category_category_type'),
        ('media', '0008_remove_subscribermediareserve_reserved_day'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='media',
            name='category',
        ),
        migrations.CreateModel(
            name='MediaCategory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='media', to='master_data.Category')),
                ('media', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='category', to='media.Media')),
            ],
            options={
                'db_table': 'media_media_category',
            },
        ),
    ]
