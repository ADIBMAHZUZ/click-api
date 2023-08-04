import os
from django.conf import settings
from rest_framework import serializers
from click.teacher_notes.models import TeacherNotesAction, NotesDownloaded, TeacherNotes, TeacherNotesDownloaded, TeacherNotesTransaction, TeacherNotesTransaction
from click.users.models import User
from click.users.serializers import UserSerializer


class TeacherSerializer(serializers.ModelSerializer):
    preview_url = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'name', 'preview_url', 'url']

    def get_preview_url(self, obj):
        serializer = UserSerializer(obj, context=self.context).data
        logo = serializer['logo']
        return logo

    def get_url(self, obj):
        serializer = UserSerializer(obj, context=self.context).data
        logo = serializer['logo']
        return logo
        
class TeacherNotesSerializer(serializers.ModelSerializer):
    teacher = TeacherSerializer(required=False, allow_null=True)
    size = serializers.SerializerMethodField()

    class Meta:
        model = NotesDownloaded
        fields = ['size','name', 'file_type', 'url', 'created_date', 'teacher']

    def get_size(self, obj):
        if obj.size is not None:
            return round(int(obj.size)/(1024*1024), 2)
        return None

# new

class TeacherNotesDetailSerializer(serializers.ModelSerializer):
    created_date = serializers.ReadOnlyField(source= 'created')
    size = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()
    is_borrowed = serializers.SerializerMethodField()

    class Meta:
        model = TeacherNotes
        fields = ['id', 'size', 'name', 'file_type', 'url', 'created_date', 'is_borrowed']
        read_only_fields = ('id',)

    def get_size(self, obj):
        if obj.size is not None:
            return round(int(obj.size)/(1024*1024), 2)
        return None

    def get_url(self, obj):
        return os.path.join(self.context['request'].build_absolute_uri('/')[:-1], settings.TEACHER_NOTES, obj.url)

    def get_is_borrowed(self, obj):
        borrowed = TeacherNotesDownloaded.objects.filter(note= obj, subscriber= self.context['request'].user).first()
        if borrowed is not None:
            return True
        return False

class TeacherNotesCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = TeacherNotes
        fields = ['size', 'name', 'file_type', 'url', 'parent_folder','teacher']

class TeacherNotesTransactionSerializer(serializers.ModelSerializer):

    class Meta:
        model = TeacherNotesTransaction
        fields = ['id', 'note', 'subscriber','action']
        read_only_fields = ('id',)

class TeacherNotesDownloadSerializer(serializers.ModelSerializer):

    class Meta:
        model = TeacherNotesDownloaded
        fields = ['id', 'note', 'subscriber']
        read_only_fields = ('id',)

class TeacherNotesDownloadedSerializer(serializers.ModelSerializer):
    url = serializers.SerializerMethodField()
    size = serializers.SerializerMethodField()
    teacher = TeacherSerializer(required=False, allow_null=True)

    class Meta:
        model = TeacherNotes
        fields = ['id', 'size', 'name', 'file_type', 'url', 'teacher']
        read_only_fields = ('id',)

    def get_url(self, obj):
        return os.path.join(self.context['request'].build_absolute_uri('/')[:-1], settings.TEACHER_NOTES, obj.url)

    def get_size(self, obj):
        if obj.size is not None:
            return round(int(obj.size)/(1024*1024), 2)
        return None
