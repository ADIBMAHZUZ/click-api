import os

from django.core.management.base import BaseCommand
from django.conf import settings
from os import listdir
from pathlib import Path

from click.users.models import User, UserType
from click.teacher_notes.models import TeacherNotes, FileType
from click.teacher_notes.serializers import TeacherNotesCreateSerializer


class Command(BaseCommand):
    def create_data(self, user_id, path):
        parent_notes = TeacherNotes.objects.filter(url= path).first()
        context_path = os.path.join(settings.MEDIA_ROOT, path)
        for name in os.listdir(context_path):
            src = os.path.join(context_path, name)
            if os.path.isdir(src):
                url = os.path.join(path, name)
                teacher_notes = TeacherNotes.objects.filter(url= url).first()
                if teacher_notes is None:
                    serializer = TeacherNotesCreateSerializer(
                        data={'name': name, 'file_type': FileType.FOLDER, 'url': url, 'teacher': user_id, 'parent_folder': parent_notes.id}
                    )
                    serializer.is_valid(raise_exception=True)
                    serializer.save()                
                self.create_data(user_id, url)
            else:
                url = os.path.join(path, str(name))
                teacher_notes = TeacherNotes.objects.filter(url= url).first()
                if teacher_notes is None:
                    serializer = TeacherNotesCreateSerializer(
                        data={'name': str(name), 'file_type': str(name).split('.')[-1], 'url': url, 'size': os.path.getsize(src), 'teacher': user_id, 'parent_folder': parent_notes.id}
                    )
                    serializer.is_valid(raise_exception=True)
                    serializer.save()

    def query_teacher(self):
        print('----------> Loading')
        list_user = User.objects.filter(user_type= UserType.TEACHER)
        for user in list_user:
            Path(os.path.join(settings.MEDIA_ROOT, settings.NOTES, str(user.id))).mkdir(parents=True, exist_ok=True)
            path = os.path.join(settings.NOTES, str(user.id))
            teacher_notes = TeacherNotes.objects.filter(url= path).first()
            if teacher_notes is None:
                serializer = TeacherNotesCreateSerializer(
                    data={'name': user.id, 'file_type': FileType.FOLDER, 'url': path, 'teacher': user.id, 'parent_folder': 0}
                )
                serializer.is_valid(raise_exception=True)
                serializer.save()
            self.create_data(user.id, path)

    def handle(self, *args, **options):
        self.query_teacher()
        print("----------------------> Success")
        # return super().handle(*args, **options)