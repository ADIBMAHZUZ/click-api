# Generated by Django 3.0.4 on 2020-06-28 02:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0007_usersactivity'),
    ]

    operations = [
        migrations.AddField(
            model_name='library',
            name='learning_material_title_en',
            field=models.CharField(default='Learning Materials', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='library',
            name='learning_material_title_ms',
            field=models.CharField(default='Bahan Pembelajaran', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='library',
            name='media_title_en',
            field=models.CharField(default='Library Books, Videos & Musics', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='library',
            name='media_title_ms',
            field=models.CharField(default='Buku Perpustakaan, Video & Muzik', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='library',
            name='school_news_board_title_en',
            field=models.CharField(default='School News Board', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='library',
            name='school_news_board_title_ms',
            field=models.CharField(default='Lembaga Berita Sekolah', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='library',
            name='student_content_title_en',
            field=models.CharField(default='Student Content', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='library',
            name='student_content_title_ms',
            field=models.CharField(default='Sejarah Sekolah', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='library',
            name='teacher_notes_title_en',
            field=models.CharField(default='Teacher Notes', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='library',
            name='teacher_notes_title_ms',
            field=models.CharField(default='Nota Guru', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='library',
            name='the_school_history_title_en',
            field=models.CharField(default='The School History', max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='library',
            name='the_school_history_title_ms',
            field=models.CharField(default='Sejarah Sekolah', max_length=100, null=True),
        ),
    ]
