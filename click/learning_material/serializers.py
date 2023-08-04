from rest_framework import serializers

from click.users.models import User, Librarian
from click.users.serializers import UserLibrarySerializer
from click.learning_material.models import Media, MediaImage, SubscriberMedia
from click.master_data.models import Category
from click.master_data.serializers import CategorySerializer


class MediaImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)

    class Meta:
        model = MediaImage
        fields = ['id', 'image', 'thumbnail', 'media']


class MediaSerializer(serializers.ModelSerializer):
    file_size = serializers.SerializerMethodField()
    url = serializers.FileField(max_length=None, use_url=True, allow_null=True, required=False)
    images = MediaImageSerializer(many=True, required=False, allow_null=True)

    class Meta:
        model = Media
        fields = ['id', 'name', 'is_active', 'library', 'category',
         'duration', 'author', 'format_type', 'media_type',
         'number_of_download', 'file_size', 'url', 'thumbnail',
         'release_date', 'isbn','images','main_category']
        read_only_fields = ('id',)

    def get_extra_kwargs(self):
        extra_kwargs = super(MediaSerializer, self).get_extra_kwargs()

        if self.instance is not None:

            kwargs = extra_kwargs.get('library', {})
            kwargs['read_only'] = True
            extra_kwargs['library'] = kwargs

        return extra_kwargs

    def get_file_size(self, obj):
        if obj.file_size is not None:
            return round(obj.file_size/(1024*1024), 2)
        return None


class SubscriberMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriberMedia
        fields = ['id', 'media', 'subscriber'] 

class LearningMaterialMediaSerializer(serializers.ModelSerializer):
    file_size = serializers.SerializerMethodField()
    url = serializers.FileField(max_length=None, use_url=True, allow_null=True, required=False)
    images = MediaImageSerializer(many=True, required=False, allow_null=True)
    category = CategorySerializer()
    library = serializers.SerializerMethodField()
    is_borrowed = serializers.SerializerMethodField()

    class Meta:
        model = Media
        fields = ['id', 'name', 'is_active', 'library', 'category',
         'duration', 'author', 'format_type', 'media_type',
         'number_of_download', 'file_size', 'url', 'thumbnail',
         'release_date', 'isbn', 'is_borrowed','images','main_category']
        read_only_fields = ('id',)

    def get_library(self, obj):
        get_library = Librarian.objects.filter(library_id = obj.library).first()
        get_user = User.objects.filter(id = get_library.user_id).first()
       
        if get_library != None:
            return UserLibrarySerializer(get_user, context={'request': self.context['request']}).data
        return None

    def get_file_size(self, obj):
        if obj.file_size is not None:
            return round(obj.file_size/(1024*1024), 2)
        return None

    def get_is_borrowed(self, obj):
        subscriberMedia = SubscriberMedia.objects.filter(media= obj, subscriber= self.context['request'].user).first()
        if subscriberMedia is not None:
            return True
        return False 