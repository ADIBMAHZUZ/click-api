from operator import itemgetter
from django.urls import clear_script_prefix
from requests import delete
from rest_framework import mixins, generics, pagination, permissions, views, status, parsers
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend
from django_filters import rest_framework as filters
from django.utils import timezone, dateformat
from django.db.models import Sum
from dateutil.relativedelta import relativedelta
from rest_framework.parsers import MultiPartParser, JSONParser
from click.master_data.models import Category
import dateutil.parser
from click.media.models import (
    MainCategory,
    Media,
    MediaImage,
    SubscriberMedia,
    LibraryMedia,
    LibraryMedia,
    SubscriberMediaFavorite,
    SubscriberMediaTransaction,
    SubscriberMediaAction,
    FileType,
    SubscriberMediaReserve,
    Encryptor,
    MediaCategory,
    Cryptography,
)
from click.media.serializers import (
    LibraryMediaSerializer,
    MediaSerializer,
    MediaImageSerializer,
    MediaForSubscriberSerializer,
    SubscriberMediaSerializer,
    SubscriberMediaBusiness,
    SubscriberMediaFavoriteSerializer,
    MediaLibrarianSerializer,
    RelatedMediaSerializer,
    PublisherMediaSerializer,
    MediaListForSubscriberSerializer,
)
from click.users.models import User, UserType, Librarian, Library, Publisher, Subscriber
from click.notification.serializers import NotificationProducerSerializer, NotificationReceiverSerializer
from click.notification.models import ConfirmMedia, ConfirmRenewMedia, NotificationReceiver, NotificationStatus, NotificationType, MessageNotification, Quotation, QuotationDetail, RequestMedia, ConfirmUpload, RequestRenewMedia, SendQuotation, UploadType

import datetime
import eyed3
import uuid
import os
import string
import random
import math
import base64

from urllib.request import urlopen
from PyPDF2 import PdfFileReader, PdfFileWriter
from io import BytesIO
from django.conf import settings
from pathlib import Path
from moviepy.video.io.ffmpeg_tools import ffmpeg_extract_subclip
from moviepy.editor import VideoFileClip
from shutil import copyfile, rmtree
from collections import OrderedDict
from django.db.models import F,Q

def plus_months_to_datetime(datetime, months_):    
    return  datetime +relativedelta(months=months_)



class MediaFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr='icontains')
    publisher = filters.CharFilter(field_name="publisher_id", lookup_expr='exact')

    class Meta:
        model = Media
        fields = ['name', 'media_type', 'publisher']


class MediaList(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MediaForSubscriberSerializer
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = MediaFilter
    ordering_fields = ['name', 'media_type']

    def get_queryset(self):
        return Media.objects.filter(library_media__library=self.request.user.subscriber.library.id, library_media__is_active=True).order_by('-id').distinct('id')

    def get_pagination_class(self):
        if self.request.user.is_subscriber():
            return None

        return pagination.PageNumberPagination

    def get(self, request, *args, **kwargs):

        category_id = request.query_params.get('category')
        media_type = request.query_params.get('media_type')
        name = request.query_params.get('name')
        if category_id is None:
            library = self.request.user.subscriber.library.id

            lastest = MediaListForSubscriberSerializer(Media.objects.getMediaForSubscriber(library, name, media_type=media_type), many=True, context={'request': request})

            categories = []

            cats = Category.objects.filter(media__media__library_media__library_id=request.user.subscriber.library_id).distinct('id')

            for cat in cats:
                mediaSerializer = MediaListForSubscriberSerializer(Media.objects.getMediaForSubscriber(library, name, cat.id, media_type), many=True, context={'request': request})
                if len(mediaSerializer.data) != 0:
                    categories.append({'category': {'id': cat.id, 'name': cat.name}, 'media': mediaSerializer.data})

            response = {'success': True, 'results': {'lastest': lastest.data, 'categories': categories}}

            return Response(response)

        category = Category.objects.filter(id=category_id).first()

        queryset = self.filter_queryset(self.get_queryset().filter(category__category_id=category_id))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            results = self.get_paginated_response(serializer.data)

            return Response({'success': True, 'results': {'category': {'id': category.id, 'name': category.name,}, 'media': results.data}})

        serializer = self.get_serializer(queryset, many=True)

        return Response({'success': True, 'results': {'category': {'id': category.id, 'name': category.name,}, 'media': serializer.data}})


class MediaDetail(mixins.RetrieveModelMixin, mixins.UpdateModelMixin, mixins.DestroyModelMixin, generics.GenericAPIView):

    serializer_class = MediaForSubscriberSerializer

    def get_queryset(self):
        return Media.objects.filter(library_media__library=self.request.user.subscriber.library.id, library_media__is_active=True)

    def get(self, request, pk):
        media = Media.objects.filter(library_media__library=self.request.user.subscriber.library.id, library_media__is_active=True, id=pk).first()
        if media is None:
            return Response({'success': False})
        serializer = self.get_serializer(media).data
        return Response({'results': serializer})

    def put(self, request, *args, **kwargs):
        # return self.update(request, *args, **kwargs)
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response({'results': serializer.data})

    def delete(self, request, *args, **kwargs):
        # return self.destroy(request, *args, **kwargs)
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubscriberMediaListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MediaForSubscriberSerializer
    pagination_class = None

    def get_queryset(self):
        get_day = datetime.datetime.now().strftime('%Y-%m-%d')
        return Media.objects.filter(
            subscriber_media_media__subscriber=self.request.user,
            library_media__is_active=True,
            subscriber_media_media__expiration_time__gt=get_day,
            library_media__library_id=self.request.user.subscriber.library_id,
        ).order_by('-id')

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(queryset, many=True)
        return Response({'results': serializer.data})


class SubscriberMediaFavoriteListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MediaForSubscriberSerializer

    def get_queryset(self, media_type=None):

        queryset = Media.objects.filter(favorites__subscriber=self.request.user, library_media__is_active=True)

        if media_type is not None:
            return queryset.filter(media_type=media_type)

        return queryset

    def get(self, request, *args, **kwargs):
        media_type = request.query_params.get('media_type')

        queryset = self.filter_queryset(self.get_queryset(media_type))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({'results': serializer.data})


class SubscriberMediaFavoriteListDetailView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MediaForSubscriberSerializer

    def post(self, request, pk, *args, **kwargs):

        media = Media.objects.filter(id=pk).first()

        if media is None:
            return Response({'success': False, 'error': 'Media is not exists'})

        subscriberMediaFavorite = SubscriberMediaFavorite.objects.filter(media_id=media.id, subscriber_id=request.user.id).first()

        if subscriberMediaFavorite is not None:
            return Response({'success': False, 'error': 'Subscriber has already favorited this media'})

        serializer = SubscriberMediaFavoriteSerializer(data={'media': media.id, 'subscriber': request.user.id})

        serializer.is_valid(raise_exception=True)
        serializer.save()

        media_serializer = MediaForSubscriberSerializer(media, context={'request': request})

        return Response({'success': True, 'media': media_serializer.data})

    def delete(self, request, pk, *args, **kwargs):

        media = Media.objects.filter(id=pk).first()

        if media is None:
            return Response({'success': False, 'error': 'Media is not exists'})

        subscriberMediaFavorite = SubscriberMediaFavorite.objects.filter(media_id=media.id, subscriber_id=request.user.id).first()

        if subscriberMediaFavorite is None:
            return Response({'success': False, 'error': 'Subscriber does not favorite this media'})

        subscriberMediaFavorite.delete()

        media_serializer = MediaForSubscriberSerializer(media, context={'request': request})

        return Response({'success': True, 'media': media_serializer.data})


class MediaBorrowView(views.APIView):
    serializer_class = MediaSerializer

    def post(self, request, pk, format=None):
        get_day = timezone.now()
        if request.data.get('expiration_time'):
            try: 
                expiration_time =  dateutil.parser.parse(request.data.get('expiration_time'))
                expiration_time =  expiration_time.astimezone(datetime.timezone.utc)
            except ImportError as exc:
                return Response({'success': False, 'error': 'Expiration time is wrong format.'})
        else:
            return Response({'success': False, 'error': 'Expiration time is required.'})

        media = Media.objects.filter(id=pk).first()
        library_media = LibraryMedia.objects.filter(media_id=pk, library=request.user.subscriber.library,
                                                    quantity__gt=0,expired_date__gt=get_day, is_active=True).order_by('-expired_date').first()
        subscriberMedia = SubscriberMedia.objects.filter(media_id=pk, subscriber=request.user).first()
        getSubscriber = Subscriber.objects.filter(user=request.user).first()
        reserve_media = SubscriberMediaReserve.objects.filter(media_id=pk, subscriber=request.user).first()        

        if getSubscriber is not None and getSubscriber.max_download <= 0:
            return Response({'success': False, 'error': 'Reach to limit borrow', 'code': 'CLICk413'})     
        if media is None:
            return Response({'success': False, 'error': 'Media does not found', 'code': 'CLICk410'})        
        if subscriberMedia is not None and subscriberMedia.expiration_time > get_day:
            return Response({'success': False, 'error': 'You have borrowed this media', 'code': 'CLICk415'})       

        if not library_media:
            return Response({'success': False, 'error': 'This media is not available', 'code': 'CLICk411'})

        if expiration_time is not None:
            if expiration_time <= get_day:
                return Response({'success': False, 'error': 'expiration time invalid', 'code': 'CLICk414'})        

        if reserve_media is not None:
            return Response({'success': False, 'error': 'You have reserved this media', 'code': 'CLICk416'})

        media.number_of_download += 1
        media.save()
        getSubscriber.max_download -= 1
        getSubscriber.save()
        library_media.quantity -= 1
        library_media.number_of_download += 1
        library_media.save()
        subscriber_transaction = SubscriberMediaTransaction.objects.create(action=SubscriberMediaAction.BORROW, media_id=pk, subscriber=request.user)
        subscriber_transaction.save()
        
        if subscriberMedia is None:            
            subscriberMedia = SubscriberMedia.objects.create(media_id=pk, subscriber=request.user, expiration_time=expiration_time,library_media_id=library_media.id)
        else:
            subscriberMedia.expiration_time = expiration_time

        if subscriberMedia.expiration_time > subscriberMedia.library_media.expired_date:
            subscriberMedia.expiration_time=subscriberMedia.library_media.expired_date
        subscriberMedia.save()

        return Response({'success': True})


class MediaExtendView(views.APIView):
    def post(self, request, pk, format=None):
        get_day = timezone.now()
        subscriberMedia = SubscriberMedia.objects.filter(media_id=pk, subscriber=request.user).first()

        if subscriberMedia is None:
            return Response({'success': False, 'error': 'You have not borrowed this media'})

        current_library_media=subscriberMedia.library_media
        duration_current_library_media=(current_library_media.expired_date-get_day).days

        expiration_time =  dateutil.parser.parse(request.data.get('expiration_time')).astimezone(datetime.timezone.utc)

        if duration_current_library_media>0:        
            subscriberMedia.expiration_time = expiration_time
            if subscriberMedia.expiration_time > current_library_media.expired_date:
                subscriberMedia.expiration_time=current_library_media.expired_date
            subscriberMedia.save()

            subscriber_transaction = SubscriberMediaTransaction.objects.create(action=SubscriberMediaAction.EXTEND, media_id=pk, subscriber=request.user)
            subscriber_transaction.save()

        return Response({'success': True})


class MediaReturnView(views.APIView):
    def post(self, request, pk, format=None):
        # media = Media.objects.filter(id=pk).first()
        libraryMedia = LibraryMedia.objects.filter(id=pk, library=request.user.subscriber.library).first()
        getSubscriber = Subscriber.objects.filter(user=request.user).first()

        if libraryMedia is not None:
            subscriberMedia = SubscriberMedia.objects.filter(library_media=libraryMedia, subscriber=request.user).first()
            if subscriberMedia is None:
                return Response({'success': False})

            subscriberMedia.expiration_time = timezone.now() - datetime.timedelta(days=1)
            subscriberMedia.save()

            libraryMedia.quantity += 1
            libraryMedia.save()

            getSubscriber.max_download += 1
            getSubscriber.save()

            log = SubscriberMedia.objects.filter(media_id=libraryMedia.media.id, subscriber_id=request.user.id)
            log.delete()

            subscriber_transaction = SubscriberMediaTransaction.objects.create(action=SubscriberMediaAction.RETURN, media_id=libraryMedia.media.id, subscriber=request.user)
            subscriber_transaction.save()
        return Response({'success': True})


class LibraryMediaFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="media__name", lookup_expr='icontains')
    publisher = filters.CharFilter(method="filter_by_publisher_id")
    media_type=filters.CharFilter(method="filter_by_media_type")
    class Meta:
        model = LibraryMedia
        fields = ['name','media_type', 'publisher']
        
    def filter_by_publisher_id(self, queryset, name, value):
        return queryset.filter(
            media__publisher_id=value
        ).distinct()
    def filter_by_media_type(self, queryset, name, value):
        return queryset.filter(
            media__media_type=value
        ).distinct()
		
		
class LibraryMediaView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = LibraryMediaFilter
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]

    def get_queryset(self):

        if self.request.user.is_librarian():
            return LibraryMedia.objects.filter(library_id=self.request.user.librarian.library.id,is_renew=False).order_by('expired_date')

    def get_serializer_class(self):
        get_user = self.request.user
        user_type = get_user.user_type
        user_id = get_user.id

        if user_type == UserType.LIBRARIAN:
            serializer_class = LibraryMediaSerializer
            return serializer_class
        return None


class MediaView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    filterset_class = MediaFilter
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]

    def get_queryset(self):
        if self.request.user.is_publisher():
            return Media.objects.filter(publisher_id=self.request.user.id).order_by('-id')

        if self.request.user.is_librarian():
            return Media.objects.filter(library_media__library=self.request.user.librarian.library.id).order_by('-id')

    def get_serializer_class(self):
        get_user = self.request.user
        user_type = get_user.user_type
        user_id = get_user.id
        serializer_class = MediaSerializer

        if user_type == UserType.PUBLISHER:
            serializer_class = MediaSerializer

        if user_type == UserType.LIBRARIAN:
            serializer_class = MediaLibrarianSerializer

        return serializer_class

    def create_preview(self, request, obj):
        path_src = os.path.join(settings.MEDIA_ROOT, str(obj.url))
        path_des = os.path.join(settings.MEDIA_ROOT, str(obj.preview_url))

        if str(obj.url).lower().endswith('.pdf'):
            src_file = open(path_src, 'rb').read()
            pdf_file = BytesIO(src_file)
            pdf_reader = PdfFileReader(pdf_file)
            pdf_write = PdfFileWriter()
            num_pages = pdf_reader.getNumPages()
            max_preview = 0
            if num_pages < 10:
                max_preview = 1
            else:
                max_preview = 10
            count = 0
            while count < max_preview:
                pdf_write.addPage(pdf_reader.getPage(count))
                count = count + 1
            desFile = open(path_des, 'wb')
            pdf_write.write(desFile)
            desFile.close()
            pdf_file.close()
        else:
            ffmpeg_extract_subclip(path_src, 0, 10, targetname=path_des)

    def duration(self, format_type, file):
        duration = None

        if format_type.lower() == 'pdf':
            pdf_reader = PdfFileReader(file)
            num_pages = pdf_reader.getNumPages()
            duration = str(num_pages) + ' pages'
        elif format_type.lower() == 'mp3':
            get_file = eyed3.load(file)
            duration = get_file.info.time_secs
            if duration > 60:
                duration = str(round(duration / 60, 1)) + ' minutes'
            else:
                duration = str(duration) + ' seconds'
        elif format_type.lower() == 'mp4':
            video = VideoFileClip(file)
            duration = video.duration
            if duration > 60:
                duration = str(round(duration / 60, 1)) + ' minutes'
            else:
                duration = str(duration) + ' seconds'
        return duration

    def checkFileType(self, file_type):
        return str(file_type).lower().endswith(("pdf", "mp3", "mp4"))

    def post(self, request):
        data = request.data.dict()
        temp_file = data.get('url')
        url_type = str(temp_file)
        isbn = data.get('isbn')

        if not request.user.is_publisher():
            return Response({'success': False, 'error': 'No permission', 'code': 'CLC400'}, status=status.HTTP_400_BAD_REQUEST)

        # if data.get('media_type') != FileType.BOOK:
        #     isbn = None

        if isbn is not None and Media.objects.filter(isbn=isbn).first() is not None:
            return Response({'success': False, 'error': 'ISBN already exist.', 'code': 'CLC401'}, status=status.HTTP_400_BAD_REQUEST)

        Path(os.path.join(settings.MEDIA_ROOT, 'media', 'temp')).mkdir(parents=True, exist_ok=True)
        Path(os.path.join(settings.MEDIA_ROOT, 'media', 'preview_url')).mkdir(parents=True, exist_ok=True)

        if not self.checkFileType(url_type):
            return Response({'success': False, 'error': 'File type must be pdf, mp3, mp4', 'code': 'CLC402'}, status=status.HTTP_400_BAD_REQUEST)

        storage = Publisher.objects.filter(user_id=request.user.id).first().storage
        file_size = os.path.getsize(temp_file.temporary_file_path())
        current_data = Media.objects.filter(publisher_id=request.user.id).aggregate(size=Sum('file_size'))
        if current_data['size'] is None:
            current_data['size'] = 0

        if file_size / (1024 * 1024) >= 700:
            return Response({'success': False, 'error': 'Your file size should be less than 700MB!', 'code': 'CLC403'}, status=status.HTTP_400_BAD_REQUEST)

        data_size = float(file_size) + float(current_data['size'])
        if data_size > storage * math.pow(1024, 3):
            return Response({'success': False, 'error': 'Not enough storage', 'code': 'CLC404'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PublisherMediaSerializer(data={**data, 'publisher': request.user.id})
        serializer.is_valid(raise_exception=True)
        media = serializer.save()

        images = request.data.getlist('images[]')

        for image in images:
            media_image = MediaImageSerializer(data={'image': image, 'media': media.id,})

            media_image.is_valid(raise_exception=True)
            media_image.save()

        get_media_image = MediaImage.objects.filter(media_id=media.id)
        thumbnail = get_media_image.first().image
        for image in get_media_image:
            image.thumbnail = thumbnail
            image.save()

        category = data.get('category')
        if category is not None:
            list_category = data.get('category').split(',')
            for category in list_category:
                media_category = MediaCategory.objects.create(media=media, category_id=int(category))
                media_category.save()

        name_url = str(media.url).split('/')
        preview_url = name_url[len(name_url) - 1]
        media.preview_url = str('media/preview_url/' + preview_url)
        format_type = str(media.url).split('.')[-1]

        path = os.path.join(settings.MEDIA_ROOT, str(media.url))
        duration = self.duration(format_type, path)
        self.create_preview(request, media)
        
        key = ''.join(random.choice(string.ascii_lowercase) for i in range(32))
        Encryptor.encrypt_file(self, media.url, media.media_type, key)

        media.encrypt_key = key
        media.format_type = format_type
        media.duration = duration
        media.file_size = file_size
        media.thumbnail = thumbnail
        media.save()

        producer = NotificationProducerSerializer(data={'user': request.user.id})
        producer.is_valid(raise_exception=True)
        noti_producer = producer.save()

        receiver = NotificationReceiverSerializer(
            data={'producer': noti_producer.id, 'notification_type': NotificationType.CONFIRM_UPLOAD, 'message': MessageNotification.LOG_UPLOAD_MEDIA, 'user': request.user.id,}
        )
        receiver.is_valid(raise_exception=True)
        noti_receiver = receiver.save()

        confirm = ConfirmUpload.objects.create(receiver=noti_receiver, upload_type=UploadType.MEDIA, name=media.name, media_type=media.media_type)
        confirm.save()
        return Response({'success': True}, status=status.HTTP_200_OK)

class LibraryMediaDetailView(generics.RetrieveDestroyAPIView):
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]
    def get_queryset(self):
        get_user = self.request.user
        user_type = get_user.user_type

        if user_type == UserType.LIBRARIAN:
            queryset = LibraryMedia.objects.filter(library_id=self.request.user.librarian.library.id)

        return queryset

    def get_serializer_class(self):
        get_user = self.request.user
        user_type = get_user.user_type

        if user_type == UserType.LIBRARIAN:
            serializer_class = LibraryMediaSerializer

        return serializer_class
    
    def perform_destroy(self, instance):

        if self.request.user.is_librarian():
            library_media = LibraryMedia.objects.filter(library_id=self.request.user.librarian.library_id, id=instance.id).first()
            library_media.is_active = not library_media.is_active
            library_media.save()

            if library_media.is_active == False:
                subscriber = Subscriber.objects.filter(library_id=self.request.user.librarian.library_id)
                list_sub = []
                for sub in subscriber:
                    list_sub.append(sub.user_id)
                    sub.max_download += 1
                    sub.save()
                subscriber_media = SubscriberMedia.objects.filter(library_media=instance, subscriber_id__in=list_sub)
                subscriber_media.delete()


class MediaDetailView(generics.RetrieveDestroyAPIView):
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]

    def get_queryset(self):
        get_user = self.request.user
        user_type = get_user.user_type
        user_id = get_user.id

        if user_type == UserType.PUBLISHER:
            queryset = Media.objects.filter(publisher_id=user_id).order_by('-id')

        if user_type == UserType.LIBRARIAN:
            queryset = Media.objects.filter(library_media__library=self.request.user.librarian.library.id)

        return queryset

    def get_serializer_class(self):
        get_user = self.request.user
        user_type = get_user.user_type
        user_id = get_user.id

        if user_type == UserType.PUBLISHER:
            serializer_class = MediaSerializer

        if user_type == UserType.LIBRARIAN:
            serializer_class = MediaLibrarianSerializer

        return serializer_class

    def patch(self, request, *args, **kwargs):
        data = request.data.dict()
        media = self.get_object()

        isbn = data.get('isbn')
        # if data.get('media_type') != FileType.BOOK:
        #     isbn = None

        if isbn is not None and Media.objects.filter(isbn=isbn).exclude(id=media.id).first() is not None:
            return Response({'success': False, 'error': 'ISBN already exist.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = PublisherMediaSerializer(media, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        get_id_del = data.get('delete_images')
        get_new_images = request.data.getlist('new_images[]')

        if get_id_del != None:
            list_images_delete = get_id_del.split(',')
            image_del = MediaImage.objects.filter(id__in=list_images_delete, media_id=media.id)

            for image in image_del:
                image.delete()

        for image in get_new_images:
            new_image = MediaImageSerializer(data={'image': image, 'media': media.id})
            new_image.is_valid(raise_exception=True)
            new_image.save()

        get_media_image = MediaImage.objects.filter(media_id=media.id)
        thumbnail = get_media_image.first().image
        for image in get_media_image:
            image.thumbnail = thumbnail
            image.save()

        media.thumbnail = thumbnail
        media.save()

        category = data.get('category')
        if category is not None:
            MediaCategory.objects.filter(media=media).delete()
            list_category = category.split(',')
            for category in list_category:
                media_category = MediaCategory.objects.create(media=media, category_id=int(category))
                media_category.save()

        return Response({'success': True}, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        if self.request.user.is_publisher():
            instance.is_active = not instance.is_active
            instance.save()

        elif self.request.user.is_librarian():
            librarymedia = LibraryMedia.objects.filter(library_id=self.request.user.librarian.library_id, media_id=instance.id).first()
            librarymedia.is_active = not librarymedia.is_active
            librarymedia.save()

            if librarymedia.is_active == False:
                subscriber = Subscriber.objects.filter(library_id=self.request.user.librarian.library_id)
                list_sub = []
                for sub in subscriber:
                    list_sub.append(sub.user_id)
                    sub.max_download += 1
                    sub.save()
                subscriber_media = SubscriberMedia.objects.filter(media=instance, subscriber_id__in=list_sub)
                subscriber_media.delete()


class SubscriberMediaFavoriteView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MediaForSubscriberSerializer

    def get_queryset(self):
        return Media.objects.filter(subscriber_media_media__subscriber=self.request.user)

    def get(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        serializer = self.get_serializer(queryset, many=True)
        return Response({'results': serializer.data})


class GetMediaView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MediaSerializer
    filterset_class = MediaFilter

    def get_queryset(self):
        if self.request.user.is_librarian():
            return Media.objects.filter(publisher_id__is_active=True, is_active=True).order_by('-id')

    

class DeleteMediaView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def delete(self, request, *args, **kwargs):
        media = Media.objects.filter(id=kwargs['pk']).first()
        user=request.user
        if not user.is_publisher():
            return Response({'success': False, 'error': 'No permission'}, status=status.HTTP_400_BAD_REQUEST)
        if media.publisher_id != user.id:
            return Response({'success': False, 'error': 'No permission'}, status=status.HTTP_400_BAD_REQUEST)
        media_in_contracts=LibraryMedia.objects.filter(media_id=media.id)
        if media_in_contracts.count()>0:
            return Response({'success': False, 'error': 'This media is in contract'})
        Media.objects.filter(id=media.id).delete()
        return Response({'success': True,'message': "Media has been permanently deleted", 'data': media.id})



class AddToCartByLibraryView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        media = request.data.get('media')
        quantity = request.data.get('quantity')
        rental_period = request.data.get('rental_period')
        media_library_renew = request.data.get('library_media')
        if media_library_renew:
            media_library= LibraryMedia.objects.filter(id=media_library_renew).first()
            if not media_library:
                return Response({'success': False,'error':'media does not exist'})
            producer = NotificationProducerSerializer(data={'user': request.user.id})
            producer.is_valid(raise_exception=True)
            noti_producer = producer.save()

            receiver = NotificationReceiverSerializer(
                        data={
                            'producer': noti_producer.id,
                            'notification_type': NotificationType.REQUEST_RENEW_MEDIA,
                            'message': MessageNotification.REQUEST_RENEW_MEDIA,
                            'is_active': True,
                            'user': media_library.media.publisher_id,
                        }
                    )
            receiver.is_valid(raise_exception=True)
            noti_receiver = receiver.save()

            #quotation from publisher send to library
            quotation=Quotation.objects.create(notification=noti_receiver)              
            request_renew_media=RequestRenewMedia.objects.create(notification_id=noti_receiver.id,media_id=media_library.media.id,quantity=quantity
                                        ,rental_period=rental_period,media_library_id=media_library.id,status=NotificationStatus.PENDING)
            request_renew_media.save()
            quotation_detail=QuotationDetail.objects.create(quotation_id=quotation.id,media_id=media_library.media.id,quantity=quantity,price=media_library.media.price,rental_period=rental_period)
            quotation.total=float(quotation_detail.price)*int(quotation_detail.quantity)*int(quotation_detail.rental_period)
            if quotation.total==0:
                quotation.ref_no="Free"
                quotation.is_send=True
            quotation.save()         
        else:
            media_id = media.split(',')
            quantity_media = quantity.split(',')
            rental_periods=rental_period.split(',')

            list_trans = list(zip(media_id, quantity_media,rental_periods))

            publisher_ids=set(Media.objects.filter(id__in=media_id).values_list('publisher_id',flat=True).distinct())
            #publisher_ids=Publisher.objects.filter(media_publisher__id__in=media_id).values_list('publisher_id',flat=True).distinct()

            producer = NotificationProducerSerializer(data={'user': request.user.id})

            producer.is_valid(raise_exception=True)
            noti_producer = producer.save()

            for publisher_id in publisher_ids: 

                receiver = NotificationReceiverSerializer(
                        data={
                            'producer': noti_producer.id,
                            'notification_type': NotificationType.REQUEST_MEDIA,
                            'message': MessageNotification.NOTI_LIBRARY_REQUEST_BUY_MEDIA,
                            'is_active': True,
                            'user': publisher_id,
                        }
                    )
                receiver.is_valid(raise_exception=True)
                noti_receiver = receiver.save()

                quotation=Quotation.objects.create(notification=noti_receiver)
                
                total=0            

                for transaction in list_trans:
                    media= Media.objects.filter(id=transaction[0]).first()
                    if media.publisher_id==publisher_id:
                        request_media = RequestMedia.objects.create(quantity=transaction[1], media_id=transaction[0],rental_period=transaction[2], notification=noti_receiver, status=NotificationStatus.PENDING,)
                        request_media.save()
                        quotation_detail=QuotationDetail.objects.create(quotation_id=quotation.id,media_id=transaction[0],quantity=transaction[1],price=media.price,rental_period=transaction[2])
                        if quotation_detail:
                            if quotation_detail.price:
                                price=quotation_detail.price
                            else:
                                price=0
                            total+=float(price)*int(quotation_detail.quantity)* int(transaction[2])
                quotation.total=total
                if quotation.total==0:
                    quotation.ref_no="Free"
                    quotation.is_send=True
                quotation.save()           

        return Response({'success': True}, status=status.HTTP_200_OK)

class QuotationView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):

        noti_id=kwargs['pk']

        notification =NotificationReceiver.objects.filter(id=noti_id,user=request.user).first()

        if notification is None:
            return Response({'success': False, 'error': 'Notification does not exist.'})

        quotation_type='quotation'
        if request.user.is_admin() or (request.user.is_publisher() and notification.notification_type==NotificationType.SEND_QUOTATION):
            quotation_type='commission'


        if (notification.notification_type==NotificationType.REQUEST_MEDIA or \
            notification.notification_type==NotificationType.REQUEST_RENEW_MEDIA) and (not request.user.is_publisher()):
            return Response({'success': False, 'error': 'No permission.'})
        if (notification.notification_type==NotificationType.CONFIRM_MEDIA or \
            notification.notification_type==NotificationType.CONFIRM_RENEW_MEDIA ) and (not request.user.is_admin()):
            return Response({'success': False, 'error': 'No permission.'})

        if notification.notification_type==NotificationType.SEND_QUOTATION:
            send_quotation= SendQuotation.objects.filter(notification_id = noti_id,notification__user=request.user).first()
            notification=send_quotation.quotation.notification

        if notification is None:
            return Response({'success': False, 'error': 'Notification does not exist.'})


        quotation=Quotation.objects.filter(notification_id=notification.id).first()
        if quotation:
            if notification.notification_type==NotificationType.SEND_QUOTATION:
                if (not request.user.is_publisher()) or (not request.user.is_librarian()) or quotation.is_send==False :
                    return Response({'success':False ,'message':'No permission'})

            if notification.notification_type==NotificationType.CONFIRM_MEDIA:
                media=ConfirmMedia.objects.filter(notification=notification).first()
                if media:
                    notification=media.request.notification
                else:
                    return Response({'success':False ,'message':'Notification does not exist.'})
            if notification.notification_type==NotificationType.CONFIRM_RENEW_MEDIA:
                media=ConfirmRenewMedia.objects.filter(notification=notification).first()
                if media:
                    notification=media.request.notification
                else:
                    return Response({'success':False ,'message':'Notification does not exist.'})
            
            library_instance = User.objects.filter(producer = notification.producer).first()
            products=[]
            publisher={
                'name':notification.user.name,
                'address':notification.user.address,
                'email':notification.user.email,
                'phone':notification.user.phone
            }
            librarian={
                'name':library_instance.name,
                'address':library_instance.address,
                'email':library_instance.email,
                'phone':library_instance.phone
            }
            
            
            total=0
            quotation_details= QuotationDetail.objects.filter(quotation_id=quotation.id)
            for quotation_detail in quotation_details:
                if quotation_detail.price:
                    price=quotation_detail.price
                else:
                    price=0
                product={
                    'title':quotation_detail.media.name,
                    'material':quotation_detail.media.media_type,
                    'price':quotation_detail.price,
                    'quantity':quotation_detail.quantity,
                    'period':quotation_detail.rental_period,
                    'total':price*quotation_detail.quantity*int(quotation_detail.rental_period)
                }
                total+=price*quotation_detail.quantity*int(quotation_detail.rental_period)
                products.append(product)
            

            
            api = {'success':True , 'results': {'products': products,'total':total,'publisher':publisher,'librarian':librarian,'ref_no':quotation.ref_no, 'is_send':quotation.is_send,'quotation_type':quotation_type,'commission':quotation.commission}}
            return Response(api)
            
        return Response({'success':False ,'message':'Quotation does not exist.'})

    def post(self, request, *args, **kwargs):
        ref_no=request.data.get('ref_no')
        noti_id=kwargs['pk']
        commission=request.data.get('commission')

        notification =NotificationReceiver.objects.filter(id=noti_id,user=request.user).first()     
        notification_type=notification.notification_type

        if (notification_type==NotificationType.REQUEST_MEDIA or \
            notification_type==NotificationType.REQUEST_RENEW_MEDIA) and \
            (not request.user.is_publisher()):
            return Response({'success': False, 'error': 'No permission.'})

        if notification_type==NotificationType.CONFIRM_MEDIA and (not request.user.is_admin()):
            return Response({'success': False, 'error': 'No permission.'})

        if notification_type==NotificationType.SEND_QUOTATION:
            send_quotation= SendQuotation.objects.filter(notification_id = noti_id,notification__user=request.user).first()
            notification=send_quotation.quotation.notification

        if notification is None:
            return Response({'success': False, 'error': 'Notification does not exist.'})
        quotation=Quotation.objects.filter(notification_id=notification.id).first()
        if quotation:                  
            if notification_type==NotificationType.SEND_QUOTATION:
                if ref_no =='' or ref_no==None:
                    return Response({'success': False,'message': 'Ref No. is required'}) 
                quotation.ref_no=ref_no
                quotation.save()    
            else:
                if commission:
                    if float(commission) <=0:
                        return Response({'success': False, 'error': 'Commission must be equal or greater than 0.'})
                    quotation.commission=float(commission)
                quotation.is_send=True
                quotation.save()

                producer = NotificationProducerSerializer(data={
                'user': request.user.id
                })
                producer.is_valid(raise_exception=True)
                noti_producer = producer.save()

                receiver = NotificationReceiverSerializer(data={
                    'producer': noti_producer.id,
                    'notification_type': NotificationType.SEND_QUOTATION,
                    'message': MessageNotification.SEND_QUOTATION,
                    'is_active': True,
                    'user': notification.producer.user.id,
                })
                receiver.is_valid(raise_exception= True)
                noti_receiver = receiver.save()
                send_quotation = SendQuotation.objects.create(
                    notification = noti_receiver,
                    quotation = quotation
                )
                send_quotation.save()
        return Response({'success': True})       

class MultiUploadMediaView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def create_preview(self, request, url, path_preview):
        if str(url).lower().endswith('.pdf'):
            src_file = open(url.temporary_file_path(), 'rb').read()
            pdf_file = BytesIO(src_file)
            pdf_reader = PdfFileReader(pdf_file)
            pdf_write = PdfFileWriter()
            num_pages = pdf_reader.getNumPages()
            max_preview = 0
            if num_pages < 10:
                max_preview = 1
            else:
                max_preview = 10
            count = 0
            while count < max_preview:
                pdf_write.addPage(pdf_reader.getPage(count))
                count = count + 1
            desFile = open(path_preview, 'wb')
            pdf_write.write(desFile)
            desFile.close()
            pdf_file.close()
        else:
            ffmpeg_extract_subclip(url.temporary_file_path(), 0, 10, targetname=path_preview)

        return None

    def active(self, value):
        return value.lower() in ("true", "True")

    def checkType(self, file):
        return str(file).lower().endswith(("pdf", "mp3", "mp4"))

    def duration(self, format_type, file):
        duration = None

        if format_type.lower() == 'pdf':
            pdf_reader = PdfFileReader(file.temporary_file_path())
            num_pages = pdf_reader.getNumPages()
            duration = str(num_pages) + ' pages'
        elif format_type.lower() == 'mp3':
            get_file = eyed3.load(file.temporary_file_path())
            duration = get_file.info.time_secs
            if duration > 60:
                duration = str(round(duration / 60, 1)) + ' minutes'
            else:
                duration = str(duration) + ' seconds'
        elif format_type.lower() == 'mp4':
            video = VideoFileClip(file.temporary_file_path())
            duration = video.duration
            if duration > 60:
                duration = str(round(duration / 60, 1)) + ' minutes'
            else:
                duration = str(duration) + ' seconds'
        return duration

    def post(self, request):
        Path(os.path.join(settings.MEDIA_ROOT, 'media', 'temp')).mkdir(parents=True, exist_ok=True)
        Path(os.path.join(settings.MEDIA_ROOT, 'media', 'preview_url')).mkdir(parents=True, exist_ok=True)

        if not request.user.is_publisher():
            return Response({'success': False, 'error': 'No permission', 'code': 'CLC400'}, status=status.HTTP_400_BAD_REQUEST)
        data = request.data.dict()

        name = data.get('name')
        media_type = data.get('media_type')
        author = data.get('author')
        is_active = data.get('is_active')
        count_image = data.get('count_image')
        url = request.data.getlist('files[]')
        images = request.data.getlist('images[]')
        category = request.data.get('category')
        count_category = request.data.get('count_category')
        price = request.data.get('price')
        main_category = request.data.get('main_category')
        release_date = request.data.get('release_date')

        list_name = name.split(',')
        list_type = media_type.split(',')
        list_author = author.split(',')
        list_active = is_active.split(',')
        list_image_count = count_image.split(',')
        list_category = category.split(',')
        list_count_category = count_category.split(',')
        list_release_date=release_date.split(',')
        list_main_category=main_category.split(',')
        list_price=price.split(',')

        list_media = list(zip(list_name, list_type, list_author, list_active, url, list_image_count,list_release_date,list_main_category,list_price))


        categories = []
        for name in list_category:
            category = Category.objects.filter(name=name).first()
            if category is None:
                return Response({'success': False, 'error': 'Category invalid', 'code': 'CLC405'})
            categories.append(category)


        file_size = 0
        for filename in url:

            if not self.checkType(filename):
                return Response({'success': False, 'error': 'File type must be pdf, mp3, mp4', 'code': 'CLC402'}, status=status.HTTP_400_BAD_REQUEST)

            size = os.path.getsize(filename.temporary_file_path())
            if size / (1024 * 1024) >= 700:
                return Response({'success': False, 'error': 'Your file size should be less than 700MB!', 'code': 'CLC403'}, status=status.HTTP_400_BAD_REQUEST)

            file_size += os.path.getsize(filename.temporary_file_path())

        storage = Publisher.objects.filter(user_id=request.user.id).first().storage
        current_data = Media.objects.filter(publisher_id=request.user.id).aggregate(size=Sum('file_size'))
        if current_data['size'] is None:
            current_data['size'] = 0
        data_size = float(file_size) + float(current_data['size'])
        if data_size > storage * math.pow(1024, 3):
            return Response({'success': False, 'error': 'Not enough storage', 'code': 'CLC404'}, status=status.HTTP_400_BAD_REQUEST)

        obj_media = []
        for media in list_media:
            name_preview = os.path.join("{}.{}".format(uuid.uuid4(), str(media[4]).split('.')[-1]))
            preview_url = os.path.join('media', 'preview_url/' + name_preview)
            path_preview = os.path.join(settings.MEDIA_ROOT, 'media', 'preview_url/' + name_preview)

            self.create_preview(request, media[4], path_preview)
            format_type = str(media[4]).split('.')[-1]
            file_size = os.path.getsize(media[4].temporary_file_path())
            duration = self.duration(format_type, media[4])

            data = Media(
                name=media[0],
                media_type=media[1],
                author=media[2],
                is_active=self.active(media[3]),
                url=media[4],
                preview_url=preview_url,
                file_size=file_size,
                duration=duration,
                format_type=format_type,
                publisher_id=request.user.id,
                release_date=media[6],
                price=float(media[8]) ,
                main_category=media[7],
            )

            obj_media.append(data)

            producer = NotificationProducerSerializer(data={'user': request.user.id})
            producer.is_valid(raise_exception=True)
            noti_producer = producer.save()

            receiver = NotificationReceiverSerializer(
                data={'producer': noti_producer.id, 'notification_type': NotificationType.CONFIRM_UPLOAD, 'message': MessageNotification.LOG_UPLOAD_MEDIA, 'user': request.user.id,}
            )
            receiver.is_valid(raise_exception=True)
            noti_receiver = receiver.save()

            confirm = ConfirmUpload.objects.create(receiver=noti_receiver, upload_type=UploadType.MEDIA, name=media[0], media_type=media[1])
            confirm.save()
        create_media = Media.objects.bulk_create(obj_media)

        image_data = []
        media_category = []
        image_num = 0
        category_num = 0

        for media in create_media:
            count = 0
            while count < int(list_image_count[create_media.index(media)]):
                data = MediaImage(media_id=media.id, image=images[image_num])
                image_num += 1
                count += 1
                image_data.append(data)

            tmp = 0
            while tmp < int(list_count_category[create_media.index(media)]):
                data = MediaCategory(media_id=media.id, category=categories[category_num])
                category_num += 1
                tmp += 1
                media_category.append(data)

        create_image_media = MediaImage.objects.bulk_create(image_data)
        create_category_media = MediaCategory.objects.bulk_create(media_category)

        for media in create_media:
            key = ''.join(random.choice(string.ascii_lowercase) for i in range(32))
            Encryptor.encrypt_file(self, media.url, media.media_type, key)

            get_image = MediaImage.objects.filter(media_id=media.id)
            for image in get_image:
                thumbnail = get_image.first().image
                image.thumbnail = thumbnail
                image.save()

            media.encrypt_key = key
            media.thumbnail = thumbnail
            media.save()

        return Response({'success': True})


class RelatedMediaView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, pk):
        media = Media.objects.filter(id=pk, library_media__library_id=request.user.subscriber.library_id, library_media__is_active=True).first()
        if media is None:
            return Response({'success': False})

        media_category = MediaCategory.objects.filter(media=media)
        list_media = []
        for category in media_category:
            related_media = (
                Media.objects.filter(category__category=category.category, library_media__library_id=request.user.subscriber.library_id, library_media__is_active=True).exclude(id=pk).order_by('-id')
            )
            for related in related_media:
                if related not in list_media:
                    list_media.append(related)

        list_results = []
        if len(list_media) >= 20:
            list_results = list_media[:20]
            data = RelatedMediaSerializer(list_results, many=True, context={'request': request}).data
            return Response({'results': data})
        else:
            related_media = Media.objects.filter(author=media.author, library_media__library_id=request.user.subscriber.library_id, library_media__is_active=True).exclude(id=pk).order_by('-id')
            for related in related_media:
                if related not in list_media:
                    list_media.append(related)

        if len(list_media) >= 20:
            list_results = list_media[:20]
            data = RelatedMediaSerializer(list_results, many=True, context={'request': request}).data
            return Response({'results': data})
        else:
            related_media = Media.objects.filter(publisher=media.publisher, library_media__library_id=request.user.subscriber.library_id, library_media__is_active=True).exclude(id=pk).order_by('-id')
            for related in related_media:
                if related not in list_media:
                    list_media.append(related)

        list_results = list_media[:20]
        data = RelatedMediaSerializer(list_results, many=True, context={'request': request}).data
        return Response({'results': data})


class ReserveMediaView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):

        if not request.user.is_subscriber():
            return Response({'success': False, 'error': 'No permission'})

        is_cancel = request.data.get('is_cancel')
        library_medias = LibraryMedia.objects.filter(media_id=pk, is_active=True, library_id=request.user.subscriber.library_id,expired_date__gt=timezone.now())
        reserve = SubscriberMediaReserve.objects.filter(media_id=pk, subscriber_id=request.user.id).first()
        subscriber_media = SubscriberMedia.objects.filter(media_id=pk, subscriber_id=request.user.id).first()
        subscriber = Subscriber.objects.filter(user_id=request.user).first()

        if subscriber_media is not None:
            return Response({'success': False, 'error': 'You have borrowed this media'})

        if reserve is not None and is_cancel == True:
            subscriber.max_download += 1
            subscriber.save()
            reserve.delete()
            return Response({'success': True, 'message': 'Canceled success'})

        if subscriber.max_download <= 0:
            return Response({'success': False, 'error': 'Reach to limit borrow'})

        if reserve is None and is_cancel == True:
            return Response({'success': False, 'error': 'You have not reserved this media '})
        if library_medias.count()==0:
            return Response({'success': False, 'error': 'Media does not exist'})
        quantity=0
        for library_media in library_medias:
            quantity+=library_media.quantity            

        quantity -= SubscriberMediaReserve.objects.filter(media_id=pk).count()
        if quantity > 0:
            return Response({'success': False, 'error': 'Media is still available'})

        if reserve is not None:
            return Response({'success': False, 'error': 'You have reserved this media'})
        

        subscriberReserve = SubscriberMediaReserve.objects.create(media_id=pk, subscriber=request.user)
        subscriberReserve.save()

        subscriber.max_download -= 1
        subscriber.save()

        return Response({'success': True, 'message': 'Reserved success'})

