import math

from rest_framework import serializers

from django.db.models import Sum
from django.contrib.auth import get_user_model
from click.learning_material.models import Media as MediaLibrary
from click.media.models import Media as MediaPublisher
from click.teacher_notes.models import TeacherNotes
User = get_user_model()

from click.users.models import Library, Librarian, Teacher, Admin, Publisher, Subscriber, UsersActivity

class UserSerializer(serializers.ModelSerializer):

    logo = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'email', 'name', 'short_name', 'address', 'phone' ,'logo', 'is_active', 'user_type','created','modified')
        read_only_fields = ('id',)
        extra_kwargs = {'password': {'write_only': True}}

    def get_extra_kwargs(self):
        extra_kwargs = super(UserSerializer, self).get_extra_kwargs()

        if self.instance is not None:
            kwargs = extra_kwargs.get('email', {})
            kwargs['read_only'] = True
            extra_kwargs['email'] = kwargs

            kwargs = extra_kwargs.get('username', {})
            kwargs['read_only'] = True
            extra_kwargs['username'] = kwargs

        return extra_kwargs

class UserSubscriberSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)
    library = serializers.SerializerMethodField()
    max_device = serializers.SerializerMethodField()
    max_borrow_duration = serializers.SerializerMethodField()
    max_download = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'email', 'name', 'short_name', 'address', 'phone' ,'logo', 'is_active', 'library','max_device', 'max_borrow_duration', 'max_download', 'user_type')
        read_only_fields = ('id',)
        extra_kwargs = {'password': {'write_only': True}}

    def get_library(self, obj):
        data = Subscriber.objects.filter(user__id = obj.id).first().library_id
        return data

    def get_max_device(self, obj):
        if self.context['request'].user.is_admin():
            data = Subscriber.objects.filter(user__id = obj.id).first().max_device
        elif self.context['request'].user.is_librarian():
            data = Subscriber.objects.filter(library__id = self.context['request'].user.librarian.library_id, user__id = obj.id).first().max_device
        return data

    def get_max_borrow_duration(self, obj):
        if self.context['request'].user.is_admin():
            data = Subscriber.objects.filter(user__id = obj.id).first().max_borrow_duration
        elif self.context['request'].user.is_librarian():
            data = Subscriber.objects.filter(library__id = self.context['request'].user.librarian.library_id, user__id = obj.id).first().max_borrow_duration
        return data

    def get_max_download(self, obj):
        if self.context['request'].user.is_admin():
            data = Subscriber.objects.filter(user__id = obj.id).first().max_download
        elif self.context['request'].user.is_librarian():
            data = Subscriber.objects.filter(library__id = self.context['request'].user.librarian.library_id, user__id = obj.id).first().max_download
        return data

class UserLibrarySerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)
    library = serializers.SerializerMethodField()
    max_subscribers = serializers.SerializerMethodField()
    number_of_current_subscribers = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'email', 'name', 'short_name', 'address', 'phone' ,'logo',\
             'is_active', 'library' , 'max_subscribers', 'number_of_current_subscribers', 'user_type')
        read_only_fields = ('id',)
        extra_kwargs = {'password': {'write_only': True}}

    def get_library(self, obj):
        data = Librarian.objects.filter(user__id = obj.id).first().library_id
        return data

    def get_max_subscribers(self, obj):
        lib_id = Librarian.objects.filter(user__id = obj.id).first().library_id
        data = Library.objects.filter(librarians__library_id = lib_id).first().max_subscribers
        return data

    def get_number_of_current_subscribers(self, obj):
        return Subscriber.objects.filter(library__librarians__user_id = obj.id).count()

class UserTeacherSerializer(serializers.ModelSerializer):
    logo = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)
    subject = serializers.SerializerMethodField()
    library = serializers.SerializerMethodField()
    storage= serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'email', 'name', 'short_name', 'address', 'phone' ,'logo', 'is_active', 'user_type', 'subject', 'library','storage')
        read_only_fields = ('id',)
        extra_kwargs = {'password': {'write_only': True}}

    def get_library(self, obj):
        data = Teacher.objects.filter(user_id = obj.id).first()
        if data is not None:
            return data.library_id
        return None

    def get_subject(self, obj):
        data = Teacher.objects.filter(user_id = obj.id).first()
        if data is not None:
            return data.subject
        return None
    def get_storage(self, obj):
        data = Teacher.objects.filter(user_id = obj.id).first()
        if data is not None:
            return data.storage
        return None


class LibrarySerializer(serializers.ModelSerializer):
    entire_background_image = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)
    media_background_image = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)
    school_news_board_background_image = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)
    teacher_notes_background_image = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)
    learning_material_background_image = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)
    the_school_history_background_image = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)
    student_content_background_image = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)
    media_title = serializers.SerializerMethodField()
    school_news_board_title = serializers.SerializerMethodField()
    teacher_notes_title = serializers.SerializerMethodField()
    learning_material_title = serializers.SerializerMethodField()
    the_school_history_title = serializers.SerializerMethodField()
    student_content_title = serializers.SerializerMethodField()



    class Meta:
        model = Library
        fields = ('__all__')

    def get_media_title(self, obj):
        if self.context['request'].META.get('HTTP_ACCEPT_LANGUAGE'):
            lang = self.context['request'].META.get('HTTP_ACCEPT_LANGUAGE')
        else:
            lang = 'en'

        return obj.get_media_title(lang)

    def get_school_news_board_title(self, obj):
        if self.context['request'].META.get('HTTP_ACCEPT_LANGUAGE'):
            lang = self.context['request'].META.get('HTTP_ACCEPT_LANGUAGE')
        else:
            lang = 'en'

        return obj.get_school_news_board_title(lang)

    def get_teacher_notes_title(self, obj):
        if self.context['request'].META.get('HTTP_ACCEPT_LANGUAGE'):
            lang = self.context['request'].META.get('HTTP_ACCEPT_LANGUAGE')
        else:
            lang = 'en'

        return obj.get_teacher_notes_title(lang)

    def get_learning_material_title(self, obj):
        if self.context['request'].META.get('HTTP_ACCEPT_LANGUAGE'):
            lang = self.context['request'].META.get('HTTP_ACCEPT_LANGUAGE')
        else:
            lang = 'en'

        return obj.get_learning_material_title(lang)

    def get_the_school_history_title(self, obj):
        if self.context['request'].META.get('HTTP_ACCEPT_LANGUAGE'):
            lang = self.context['request'].META.get('HTTP_ACCEPT_LANGUAGE')
        else:
            lang = 'en'

        return obj.get_the_school_history_title(lang)

    def get_student_content_title(self, obj):
        if self.context['request'].META.get('HTTP_ACCEPT_LANGUAGE'):
            lang = self.context['request'].META.get('HTTP_ACCEPT_LANGUAGE')
        else:
            lang = 'en'

        return obj.get_student_content_title(lang)


class UserPublisherSerializer(serializers.ModelSerializer):
    storage = serializers.SerializerMethodField()
    current_storage = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'email', 'name', 'short_name', 'address', 'phone' ,'logo', 'is_active', 'user_type', 'storage', 'current_storage')
        read_only_fields = ('id',)
        extra_kwargs = {'password': {'write_only': True}}

    def get_storage(self, obj):
        user = Publisher.objects.filter(user_id = obj.id).first()
        if user is not None:
            return user.storage
        return None

    def get_current_storage(self, obj):
        media =  MediaPublisher.objects.filter(publisher_id = obj.id).aggregate(size = Sum('file_size'))
        if media['size'] is not None:
            current_storage = round(int(media['size']) / (math.pow(1024, 3)), 2)
            return current_storage
        return 0.0

class LibrarianSerializer(serializers.ModelSerializer):
    current_storage = serializers.SerializerMethodField()
    class Meta:
        model = Librarian
        fields = ('library_id', 'user_id','storage', 'current_storage')
    def get_current_storage(self, obj):
        media =  MediaLibrary.objects.filter(library_id = obj.library_id).aggregate(size = Sum('file_size'))
        teacher=Teacher.objects.filter(library_id = obj.library_id).aggregate(storage = Sum('storage'))
        current_storage=0
        if media['size'] is not None :
            current_storage += round(int(media['size']) / (math.pow(1024, 3)), 2)
        if teacher['storage'] is not None :
            current_storage += round(teacher['storage'],2)
        return current_storage

class TeacherSerializer(serializers.ModelSerializer):
    current_storage = serializers.SerializerMethodField()
    storage=serializers.SerializerMethodField()

    class Meta:
        model = Teacher
        fields = ('subject', 'library_id', 'user_id','storage', 'current_storage')
    def get_current_storage(self, obj):
        current_data = TeacherNotes.objects.filter(teacher_id=obj.user.id).aggregate(size=Sum('size'))
        if current_data['size'] is not None:
            current_storage = round(int(current_data['size']) / (math.pow(1024, 3)), 2)
            return current_storage
        return 0.0
    def get_storage(self, obj):
        return obj.storage

class PublisherSerializer(serializers.ModelSerializer):
    current_storage = serializers.SerializerMethodField()

    class Meta:
        model = Publisher
        fields = ('storage', 'current_storage', 'user_id')

    def get_current_storage(self, obj):
        media =  MediaPublisher.objects.filter(publisher_id = obj.user_id).aggregate(size = Sum('file_size'))
        if media['size'] is not None:
            current_storage = round(int(media['size']) / (math.pow(1024, 3)), 2)
            return current_storage
        return 0.0


class SubscriberSerializer(serializers.ModelSerializer):

    class Meta:
        model = Subscriber
        fields = ('user_id', 'library_id', 'max_device', 'max_borrow_duration', 'max_download', 'birthday')


class AdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = Admin
        fields = '__all__'

class ViewAllPublisherSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'name')

class UsersActivitieSerializer(serializers.ModelSerializer):
    time = serializers.ReadOnlyField(source= 'created')
    name = serializers.SerializerMethodField()

    class Meta:
        model = UsersActivity
        fields = ('user_id', 'name', 'action', 'time')

    def get_name(self, obj):
        return obj.user.name