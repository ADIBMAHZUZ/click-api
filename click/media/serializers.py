from rest_framework import serializers

# from click.users.models import Library, Teacher, Subscriber, User
from click.users.serializers import UserSerializer
from click.media.models import Media, MediaImage, LibraryMedia, SubscriberMedia, SubscriberMediaTransaction, SubscriberMediaFavorite, SubscriberMediaReserve, MediaCategory
from click.master_data.models import Category
from click.master_data.serializers import CategorySerializer
from click.users.models import UserType, Librarian, User, Subscriber
from django.utils import timezone
import datetime


class MediaImageSerializer(serializers.ModelSerializer):
    image = serializers.ImageField(max_length=None, use_url=True, allow_null=True, required=False)

    class Meta:
        model = MediaImage
        fields = ['id', 'image', 'thumbnail', 'media']


class MediaCategorySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()
    id = serializers.SerializerMethodField()

    class Meta:
        model = MediaCategory
        fields = ['id', 'name']

    def get_id(self, obj):
        category_id = Category.objects.filter(id=obj.category_id).first().id
        return category_id

    def get_name(self, obj):
        category = Category.objects.filter(id=obj.category_id).first().name
        return category


class MediaSerializer(serializers.ModelSerializer):
    file_size = serializers.SerializerMethodField()
    images = MediaImageSerializer(many=True, required=False, allow_null=True)
    category = MediaCategorySerializer(many=True, required=False, allow_null=True)
    publisher_name=serializers.SerializerMethodField()

    class Meta:
        model = Media
        fields = [
            'id',
            'name',
            'publisher',
            'category',
            'duration',
            'author',
            'file_size',
            'encrypt_key',
            'format_type',
            'media_type',
            'number_of_download',
            'url',
            'preview_url',
            'max_preview',
            'thumbnail',
            'encrypt_info',
            'name_encrypt',
            'name_backup',
            'is_active',
            'release_date',
            'isbn',
            'images',
            'price',
            'publisher_name',
            'main_category'
        ]

    def get_file_size(self, obj):
        if obj.file_size is not None:
            return round(obj.file_size / (1024 * 1024), 2)
        return None
    def get_publisher_name(self, obj):
        return obj.publisher.name

class LibraryMediaSerializer(serializers.ModelSerializer):
    media = MediaSerializer(many=False, required=False, allow_null=True)

    class Meta:
        model = LibraryMedia
        fields = ['id', 'media', 'number_of_download',
         'quantity', 'expired_date','is_active','is_renew','rental_period']



class MediaLibrarianSerializer(serializers.ModelSerializer):
    quantity = serializers.SerializerMethodField()
    publisher_active = serializers.ReadOnlyField(source='is_active')
    library_active = serializers.SerializerMethodField()
    images = MediaImageSerializer(many=True, required=False, allow_null=True)
    publisher_name = serializers.SerializerMethodField()

    class Meta:
        model = Media
        fields = ['id', 'name', 'author', 'media_type', 'thumbnail', 'url', 'preview_url', 'number_of_download', 'quantity', 'isbn', 'publisher_name', 'publisher_active', 'library_active', 'images','price','main_category',]

    def get_quantity(self, objects):
        user = self.context['request'].user

        if user.id != None:
            user_type = user.user_type
            if user_type == UserType.LIBRARIAN:
                lib_id = Librarian.objects.get(user_id=user.id).library_id
                quantity = LibraryMedia.objects.filter(library_id=lib_id, media_id=objects.id).first()
                if quantity != None:
                    return quantity.quantity
        return None

    def get_publisher_name(self, obj):
        return User.objects.filter(id=obj.publisher_id).first().name

    def get_library_active(self, obj):
        return LibraryMedia.objects.filter(media_id=obj.id, library_id= self.context['request'].user.librarian.library_id).first().is_active


# class LibraryMediaSerializer(serializers.ModelSerializer):
#     media_type= serializers.SerializerMethodField()
#     class Meta:
#         model = LibraryMedia
#         fields = ['id', 'quantity', 'is_active', 'library', 'media','rental_period','media_type','is_renew']

#     def get_media_type(self, obj):
#         return Media.objects.filter(id=obj.media_id).first().media_type


class SubscriberMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriberMedia
        fields = ['id', 'media', 'subscriber', 'expiration_time','library_media']


class SubscriberMediaTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriberMediaTransaction
        fields = ['id', 'media', 'subscriber', 'action']


class SubscriberMediaFavoriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriberMediaFavorite
        fields = ['id', 'media', 'subscriber']


# Business Logic
class MediaForSubscriberSerializer(serializers.ModelSerializer):
    category = MediaCategorySerializer(many=True, required=False, allow_null=True)
    publisher = UserSerializer()
    images = MediaImageSerializer(many=True)
    subscriber_media = serializers.SerializerMethodField()
    favorite = serializers.SerializerMethodField()
    number_of_favorites = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()
    remaining_borrow_times = serializers.SerializerMethodField()
    is_borrowed = serializers.SerializerMethodField()
    reserved_index = serializers.SerializerMethodField()

    class Meta:
        model = Media
        fields = [
            'id',
            'name',
            'publisher',
            'category',
            'duration',
            'author',
            'file_size',
            'encrypt_key',
            'format_type',
            'media_type',
            'number_of_download',
            'url',
            'preview_url',
            'max_preview',
            'thumbnail',
            'encrypt_info',
            'name_encrypt',
            'name_backup',
            'is_active',
            'quantity',
            'favorite',
            'number_of_favorites',
            'subscriber_media',
            'isbn',
            'images',
            'remaining_borrow_times',
            'is_borrowed',
            'reserved_index',
            'price',
            'main_category',
        ]

    def get_favorite(self, obj):
        subscriber_media = SubscriberMediaFavorite.objects.filter(media=obj.id, subscriber_id=self.context['request'].user.id).first()

        if subscriber_media:
            return True
        else:
            return False

    def get_number_of_favorites(self, obj):
        return SubscriberMediaFavorite.objects.filter(media=obj.id).count()

    def get_subscriber_media(self, obj):
        subscriber_media = SubscriberMedia.objects.filter(media=obj.id, subscriber_id=self.context['request'].user.id).first()

        if subscriber_media:
            serializer = SubscriberMediaSerializer(subscriber_media)

            return serializer.data
        else:
            return None

    def get_quantity(self, obj):
        library_medias = LibraryMedia.objects.filter(media=obj.id, library_id=self.context['request'].user.subscriber.library.id,
                                                    expired_date__gt=timezone.now(),is_active=True)
        quantity=0
        for library_media in library_medias:
            quantity+=library_media.quantity
        reserve = SubscriberMediaReserve.objects.filter(media=obj).count()
        quantity -=reserve
        if quantity<0:
            return 0
        return quantity

    def get_file_size(self, obj):
        if obj.file_size is not None:
            return round(obj.file_size / (1024 * 1024), 2)
        return None

    def get_remaining_borrow_times(self, obj):
        user = self.context['request'].user
        if user.is_subscriber():
            max_download = Subscriber.objects.filter(user_id=user.id).first().max_download
            return max_download
        return None

    def get_is_borrowed(self, obj):
        user = self.context['request'].user
        get_day = datetime.datetime.now().strftime('%Y-%m-%d')
        if user.is_subscriber():
            subscriber_media = SubscriberMedia.objects.filter(subscriber=user, expiration_time__gt=get_day, media=obj).first()
            if subscriber_media is not None:
                return True
        return False

    def get_reserved_index(self, obj):
        reserve = SubscriberMediaReserve.objects.filter(media=obj).order_by('id')
        if reserve.first() is not None:
            try:
                index = [media.subscriber_id for media in reserve].index(self.context['request'].user.id) + 1
            except:
                index = 0
            return index
        return 0


class SubscriberMediaBusiness(serializers.ModelSerializer):
    category = MediaCategorySerializer(many=True, required=False, allow_null=True)
    publisher = UserSerializer()
    images = MediaImageSerializer(many=True)
    subscriber_media = serializers.SerializerMethodField()
    favorite = serializers.SerializerMethodField()
    number_of_favorites = serializers.SerializerMethodField()
    quantity = serializers.SerializerMethodField()
    file_size = serializers.SerializerMethodField()

    class Meta:
        model = Media
        fields = [
            'id',
            'name',
            'publisher',
            'category',
            'duration',
            'author',
            'file_size',
            'encrypt_key',
            'format_type',
            'media_type',
            'number_of_download',
            'url',
            'preview_url',
            'max_preview',
            'thumbnail',
            'encrypt_info',
            'name_encrypt',
            'name_backup',
            'is_active',
            'quantity',
            'favorite',
            'number_of_favorites',
            'subscriber_media',
            'isbn',
            'images',
            'price',
            'main_category',
        ]

    def get_favorite(self, obj):
        subscriber_media = SubscriberMediaFavorite.objects.filter(media=obj.id, subscriber_id=self.context['request'].user.id).first()

        if subscriber_media:
            return True

        else:
            return False

    def get_number_of_favorites(self, obj):
        return SubscriberMediaFavorite.objects.filter(media=obj.id).count()

    def get_subscriber_media(self, obj):
        subscriber_media = SubscriberMedia.objects.filter(media=obj.id, subscriber_id=self.context['request'].user.id, expiration_time__gte=timezone.now()).first()

        if subscriber_media:
            serializer = SubscriberMediaSerializer(subscriber_media)

            return serializer.data
        else:
            return None

    def get_quantity(self, obj):
        library_media = LibraryMedia.objects.filter(media=obj.id, library_id=self.context['request'].user.subscriber.library.id).first()

        if library_media:
            return library_media.quantity

        else:
            return 0

    def get_file_size(self, obj):
        if obj.file_size is not None:
            return round(obj.file_size / (1024 * 1024), 2)
        return None


class RelatedMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = [
            'id',
            'name',
            'thumbnail',
            'media_type',
        ]


class ReserveMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriberMediaReserve
        fields = (
            'id',
            'media',
            'subscriber',
        )


class PublisherMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = [
            'id',
            'name',
            'publisher',
            'duration',
            'author',
            'file_size',
            'encrypt_key',
            'format_type',
            'media_type',
            'number_of_download',
            'url',
            'preview_url',
            'max_preview',
            'thumbnail',
            'encrypt_info',
            'name_encrypt',
            'name_backup',
            'is_active',
            'release_date',
            'isbn',
            'price',
            'main_category',
        ]


class MediaListForSubscriberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Media
        fields = [
            'id',
            'name',
            'thumbnail',
        ]

