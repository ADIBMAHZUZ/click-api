# Generated by Django 3.0.4 on 2020-05-09 00:10

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100)),
                ('name_malay', models.CharField(max_length=100, null=True)),
                ('description', models.CharField(max_length=500, null=True)),
                ('category_type', models.IntegerField()),
                ('is_active', models.BooleanField(default=True)),
            ],
            options={
                'db_table': 'master_data_category',
            },
        ),
    ]
