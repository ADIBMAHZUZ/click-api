# Generated by Django 3.0.4 on 2020-05-09 00:10

import click.users.models
from django.conf import settings
import django.contrib.auth.models
import django.contrib.auth.validators
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import model_utils.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('username', models.CharField(error_messages={'unique': 'A user with that username already exists.'}, max_length=150, unique=True, validators=[django.contrib.auth.validators.UnicodeUsernameValidator()], verbose_name='username')),
                ('is_staff', models.BooleanField(default=False, verbose_name='staff status')),
                ('is_active', models.BooleanField(default=True, verbose_name='active')),
                ('email', models.EmailField(max_length=254, unique=True)),
                ('user_type', models.CharField(choices=[('admin', 'Admin'), ('subscriber', 'Subscriber'), ('teacher', 'Teacher'), ('librarian', 'Librarian'), ('publisher', 'Publisher')], max_length=50)),
                ('activate_token', models.CharField(blank=True, max_length=40, null=True)),
                ('activate_time', models.DateTimeField(blank=True, null=True)),
                ('name', models.CharField(blank=True, max_length=100, null=True)),
                ('short_name', models.CharField(blank=True, max_length=100, null=True)),
                ('address', models.CharField(blank=True, max_length=500, null=True)),
                ('phone', models.CharField(blank=True, max_length=20, null=True)),
                ('logo', models.ImageField(null=True, upload_to=click.users.models.user_logo_directory_path)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.Group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.Permission', verbose_name='user permissions')),
            ],
            options={
                'db_table': 'users_user',
            },
            managers=[
                ('objects', django.contrib.auth.models.UserManager()),
            ],
        ),
        migrations.CreateModel(
            name='Library',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', model_utils.fields.AutoCreatedField(default=django.utils.timezone.now, editable=False, verbose_name='created')),
                ('modified', model_utils.fields.AutoLastModifiedField(default=django.utils.timezone.now, editable=False, verbose_name='modified')),
                ('is_active', models.BooleanField(default=True)),
                ('number_of_subscribers', models.IntegerField(default=0)),
                ('entire_background_type', models.CharField(max_length=100, null=True)),
                ('entire_background_image', models.ImageField(null=True, upload_to=click.users.models.entire_background_image_directory_path)),
                ('entire_background_color', models.CharField(max_length=100, null=True)),
                ('media_title_color', models.CharField(max_length=100, null=True)),
                ('media_border_color', models.CharField(max_length=100, null=True)),
                ('media_badge_color', models.CharField(max_length=100, null=True)),
                ('media_icon_color', models.CharField(max_length=100, null=True)),
                ('media_background_transparent', models.CharField(max_length=100, null=True)),
                ('media_background_type', models.CharField(max_length=100, null=True)),
                ('media_background_color', models.CharField(max_length=100, null=True)),
                ('media_background_image', models.ImageField(null=True, upload_to=click.users.models.media_background_image_directory_path)),
                ('school_news_board_title_color', models.CharField(max_length=100, null=True)),
                ('school_news_board_border_color', models.CharField(max_length=100, null=True)),
                ('school_news_board_badge_color', models.CharField(max_length=100, null=True)),
                ('school_news_board_icon_color', models.CharField(max_length=100, null=True)),
                ('school_news_board_background_transparent', models.CharField(max_length=100, null=True)),
                ('school_news_board_background_type', models.CharField(max_length=100, null=True)),
                ('school_news_board_background_color', models.CharField(max_length=100, null=True)),
                ('school_news_board_background_image', models.ImageField(null=True, upload_to=click.users.models.school_news_board_background_image_directory_path)),
                ('teacher_notes_title_color', models.CharField(max_length=100, null=True)),
                ('teacher_notes_border_color', models.CharField(max_length=100, null=True)),
                ('teacher_notes_badge_color', models.CharField(max_length=100, null=True)),
                ('teacher_notes_icon_color', models.CharField(max_length=100, null=True)),
                ('teacher_notes_background_transparent', models.CharField(max_length=100, null=True)),
                ('teacher_notes_background_type', models.CharField(max_length=100, null=True)),
                ('teacher_notes_background_color', models.CharField(max_length=100, null=True)),
                ('teacher_notes_background_image', models.ImageField(null=True, upload_to=click.users.models.teacher_notes_background_image_directory_path)),
                ('learning_material_title_color', models.CharField(max_length=100, null=True)),
                ('learning_material_border_color', models.CharField(max_length=100, null=True)),
                ('learning_material_badge_color', models.CharField(max_length=100, null=True)),
                ('learning_material_icon_color', models.CharField(max_length=100, null=True)),
                ('learning_material_background_transparent', models.CharField(max_length=100, null=True)),
                ('learning_material_background_type', models.CharField(max_length=100, null=True)),
                ('learning_material_background_color', models.CharField(max_length=100, null=True)),
                ('learning_material_background_image', models.ImageField(null=True, upload_to=click.users.models.learning_material_background_image_directory_path)),
                ('the_school_history_title_color', models.CharField(max_length=100, null=True)),
                ('the_school_history_border_color', models.CharField(max_length=100, null=True)),
                ('the_school_history_icon_color', models.CharField(max_length=100, null=True)),
                ('the_school_history_badge_color', models.CharField(max_length=100, null=True)),
                ('the_school_history_background_transparent', models.CharField(max_length=100, null=True)),
                ('the_school_history_background_type', models.CharField(max_length=100, null=True)),
                ('the_school_history_background_color', models.CharField(max_length=100, null=True)),
                ('the_school_history_background_image', models.ImageField(null=True, upload_to=click.users.models.the_school_history_background_image_directory_path)),
                ('student_content_title_color', models.CharField(max_length=100, null=True)),
                ('student_content_border_color', models.CharField(max_length=100, null=True)),
                ('student_content_icon_color', models.CharField(max_length=100, null=True)),
                ('student_content_badge_color', models.CharField(max_length=100, null=True)),
                ('student_content_background_transparent', models.CharField(max_length=100, null=True)),
                ('student_content_background_type', models.CharField(max_length=100, null=True)),
                ('student_content_background_color', models.CharField(max_length=100, null=True)),
                ('student_content_background_image', models.ImageField(null=True, upload_to=click.users.models.student_content_background_image_directory_path)),
            ],
            options={
                'db_table': 'users_library',
            },
        ),
        migrations.CreateModel(
            name='Token',
            fields=[
                ('key', models.CharField(max_length=40, primary_key=True, serialize=False, verbose_name='Key')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('device', models.CharField(max_length=100, null=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='auth_tokens', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'users_token',
            },
        ),
        migrations.CreateModel(
            name='Teacher',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subject', models.CharField(blank=True, max_length=50, null=True)),
                ('library', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='teachers', to='users.Library')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='teacher', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'users_teacher',
            },
        ),
        migrations.CreateModel(
            name='Subscriber',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('max_device', models.SmallIntegerField(default=4)),
                ('max_borrow_duration', models.SmallIntegerField(default=10)),
                ('max_download', models.SmallIntegerField(default=5)),
                ('birthday', models.DateField(null=True)),
                ('library', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='subscribers', to='users.Library')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='subscriber', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'users_subscriber',
            },
        ),
        migrations.CreateModel(
            name='Publisher',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='publisher', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Librarian',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('library', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='librarians', to='users.Library')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='librarian', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'db_table': 'users_librarian',
            },
        ),
        migrations.CreateModel(
            name='ForgotPasswordToken',
            fields=[
                ('key', models.CharField(max_length=40, primary_key=True, serialize=False, verbose_name='Key')),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='Created')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='auth_forgot_password_token', to=settings.AUTH_USER_MODEL, verbose_name='User')),
            ],
            options={
                'db_table': 'users_forgot_password_token',
            },
        ),
        migrations.CreateModel(
            name='Admin',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='admin', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]