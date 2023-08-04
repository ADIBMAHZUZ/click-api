from django.shortcuts import render
from django_filters import rest_framework as filters
from django.http import QueryDict
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import authenticate
from django.conf import settings

from rest_framework import generics, mixins, parsers, serializers, status, permissions, views
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, JSONParser

from click.learning_material.models import Media, MediaImage, SubscriberMedia, SubscriberMediaTransaction, SubscriberMediaAction, FileType
from click.learning_material.serializers import MediaSerializer, MediaImageSerializer, LearningMaterialMediaSerializer
from click.users.models import Teacher, User, Librarian, Subscriber, UserType
from click.master_data.models import Category
from click.master_data.serializers import CategorySerializer
from click.notification.models import NotificationStatus, MessageNotification, ConfirmUpload, UploadType, NotificationType
from click.notification.serializers import NotificationProducerSerializer, NotificationReceiverSerializer

from PyPDF2 import PdfFileReader, PdfFileWriter
import os
import eyed3
from moviepy.editor import VideoFileClip
from django.db.models import Sum
import math
class MediaFilter(filters.FilterSet):
    name = filters.CharFilter(field_name="name", lookup_expr='icontains')

    class Meta:
        model = Media
        fields = ['name', 'library', 'category', 'author', 'media_type']


class MediaView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser, parsers.FormParser]
    serializer_class = MediaSerializer
    filterset_class = MediaFilter
    ordering_fields = ['name']

    def get_queryset(self):
        if self.request.user.is_librarian():
            return Media.objects.filter(library_id = self.request.user.librarian.library_id).order_by('-id')
        
        elif self.request.user.is_subscriber():
            return Media.objects.filter(library_id = self.request.user.subscriber.library_id).order_by('-id')

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

    def post(self, request):
        data = request.data.dict()
        isbn = data.get('isbn')
        url=data.get('url')

        

        if not request.user.is_librarian():
            return Response({'success':False, 'error': 'No permission'}, status=status.HTTP_400_BAD_REQUEST)

        librarian=request.user.librarian

        file_size = os.path.getsize(url.temporary_file_path())
        storage = Librarian.objects.filter(user_id=request.user.id).first().storage

        media =  Media.objects.filter(library_id = librarian.library_id).aggregate(size = Sum('file_size'))
        teacher=Teacher.objects.filter(library_id = librarian.library_id).aggregate(storage = Sum('storage'))
        current_data=0
        if media['size'] is not None :
            current_data += float(media['size'])
        if teacher['storage'] is not None :
            current_data += float(teacher['storage'])* math.pow(1024, 3)

        if file_size / (1024 * 1024) >= 700:
            return Response({'success': False, 'error': 'Your file size should be less than 700MB!', 'code': 'CLC403'}, status=status.HTTP_400_BAD_REQUEST)

        data_size = float(file_size) + current_data
        if data_size > storage * math.pow(1024, 3):
            return Response({'success': False, 'error': 'Not enough storage', 'code': 'CLC404'}, status=status.HTTP_400_BAD_REQUEST)

        # if data.get('media_type') != FileType.BOOK:
        #     isbn = None
        
        if isbn is not None and Media.objects.filter(isbn = isbn).first() is not None:
            return Response({'success':False, 'error': 'ISBN already exist.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = MediaSerializer(data={
            **data,
            'isbn':isbn,
            'library': request.user.librarian.library.id
        })
        serializer.is_valid(raise_exception=True)
        media = serializer.save()

        images = request.data.getlist('images[]')

        for image in images:
            media_image = MediaImageSerializer(data={
                'image': image,
                'media': media.id,
            })

            media_image.is_valid(raise_exception=True)
            media_image.save()

        get_media_image = MediaImage.objects.filter(media_id= media.id)
        thumbnail = get_media_image.first().image
        for image in get_media_image:
            image.thumbnail = thumbnail
            image.save()

        media.thumbnail = thumbnail
        url = os.path.join(settings.MEDIA_ROOT, str(media.url))
        media.file_size = os.path.getsize(url)
        format_type = str(media.url).split('.')[-1]
        duration = self.duration(format_type, url)
        media.format_type = format_type
        media.duration = duration
        media.save()        

        producer = NotificationProducerSerializer(data={
            'user': request.user.id
        })
        producer.is_valid(raise_exception=True)
        noti_producer = producer.save()

        receiver = NotificationReceiverSerializer(data={
                'producer': noti_producer.id,
                'notification_type': NotificationType.CONFIRM_UPLOAD,
                'message': MessageNotification.LOG_UPLOAD_LEARNING_MATERIAL,
                'user': User.objects.filter(user_type= UserType.ADMIN).first().id,
            })
        receiver.is_valid(raise_exception= True)
        noti_receiver = receiver.save()

        confirm = ConfirmUpload.objects.create(
            receiver = noti_receiver,
            upload_type = UploadType.LEARNING_MATERIAL,
            name = media.name,
            media_type = media.media_type
        )
        confirm.save()    
        return Response({'success':True}, status=status.HTTP_201_CREATED)

class MediaDetailView(generics.RetrieveUpdateDestroyAPIView):
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser, parsers.FormParser]
    serializer_class = MediaSerializer

    def get_queryset(self):
        if self.request.user.is_librarian():
            return Media.objects.filter(library_id = self.request.user.librarian.library_id).order_by('-id')
        
        elif self.request.user.is_subscriber():
            return Media.objects.filter(library_id = self.request.user.subscriber.library_id).order_by('-id')

    def patch(self, request, *args, **kwargs):
        media = self.get_object()
        data = request.data.dict()

        if not request.user.is_librarian():
            return Response({'success':False, 'error': 'No permission'}, status=status.HTTP_400_BAD_REQUEST)

        isbn = data.get('isbn')
        # if data.get('media_type') != FileType.BOOK:
        #     isbn = None

        if isbn is not None and Media.objects.filter(isbn = isbn).exclude(id = media.id).first() is not None:
            return Response({'success':False, 'error': 'ISBN already exist.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = MediaSerializer(media, data={**data, 'isbn':isbn}, partial= True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        get_id_del = data.get('delete_images')
        get_new_images = request.data.getlist('new_images[]')

        if get_id_del != None:
            list_images_delete = get_id_del.split(',')
            image_del = MediaImage.objects.filter(id__in= list_images_delete, media_id = media.id)

            for image in image_del:
                image.delete()
        for image in get_new_images:
            new_image = MediaImageSerializer(data={'image': image, 'media': media.id})
            new_image.is_valid(raise_exception=True)
            new_image.save()
        
        get_media_image = MediaImage.objects.filter(media_id = media.id)
        thumbnail = get_media_image.first().image
        for media_image in get_media_image:
            media_image.thumbnail = thumbnail
            media_image.save()
        
        url = os.path.join(settings.MEDIA_ROOT, str(media.url))
        format_type = str(media.url).split('.')[-1]
        duration = MediaView.duration(self, format_type, url)

        media.file_size = os.path.getsize(url)
        media.thumbnail = thumbnail
        media.format_type = format_type
        media.duration = duration
        media.save()

        return Response({'success': True, 'data': serializer.data}, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        instance.is_active = not instance.is_active
        instance.save()

        if instance.is_active == False:
            subscriber = Subscriber.objects.filter(library_id = self.request.user.librarian.library_id)
            list_sub = []
            for sub in subscriber:
                list_sub.append(sub.user_id)
            subscriber_media = SubscriberMedia.objects.filter(media = instance, subscriber__in= list_sub)
            subscriber_media.delete()

# mobile

class LearningMaterialUserView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        name_search = request.query_params.get('name')
        type_search = request.query_params.get('media_type')
        if request.user.is_subscriber():
            list_category = Category.objects.all()
            categories = []
            for category in list_category:
                
                if name_search is None and type_search is None:
                    queryset = Media.objects.filter(category = category.id, library = request.user.subscriber.library_id, is_active= True)
                elif name_search is None:
                    queryset = Media.objects.filter(category = category.id, media_type__exact = type_search, library = request.user.subscriber.library_id, is_active= True)
                elif type_search is None:
                    queryset = Media.objects.filter(category = category.id, name__icontains = name_search, library = request.user.subscriber.library_id, is_active= True)
                else:
                    queryset = Media.objects.filter(category = category.id, name__icontains = name_search, media_type__exact = type_search, library = request.user.subscriber.library_id, is_active= True)
                serializer = LearningMaterialMediaSerializer(queryset, many=True, context = {'request':request})
                data = {'category': {'id':category.id, 'name': category.name}, 'media': serializer.data }
                categories.append(data)
            api = {'success':True , 'results': {'categories': categories}}
            return Response(api, status= status.HTTP_200_OK)
        else:
            return Response({'error': 'no permission'}, status=status.HTTP_200_OK)

class LearningMaterialCategoryDetailView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LearningMaterialMediaSerializer

    def get(self, request, id):
        name_search = request.query_params.get('name')
        type_search = request.query_params.get('media_type')
        if request.user.is_subscriber():
            category = Category.objects.filter(id = id).first()
            if category is not None:
                if name_search is None and type_search is None:
                    queryset = Media.objects.filter(category = category.id, library = request.user.subscriber.library_id, is_active= True)
                elif name_search is None:
                    queryset = Media.objects.filter(category = category.id, media_type__exact = type_search, library = request.user.subscriber.library_id, is_active= True)
                elif type_search is None:
                    queryset = Media.objects.filter(category = category.id, name__icontains = name_search, library = request.user.subscriber.library_id, is_active= True)
                else:
                    queryset = Media.objects.filter(category = category.id, name__icontains = name_search, media_type__exact = type_search, library = request.user.subscriber.library_id, is_active= True)
                page = self.paginate_queryset(queryset)
                if queryset is not None:
                    serializer = LearningMaterialMediaSerializer(page, many=True, context = {'request':request})
                    result = self.get_paginated_response(serializer.data)
                    data = {'category': {'id':category.id, 'name': category.name}, 'media': result.data }
                api = {'success':True , 'results': data}
                return Response(api, status=status.HTTP_200_OK)
            else:
                data = []
                api = {'success':True , 'results': data}
                return Response(api, status=status.HTTP_200_OK)
        else:
            return Response({'error':'no permission'}, status=status.HTTP_200_OK)

class LearningMaterialUserDetailView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        if request.user.is_subscriber():
            media = Media.objects.filter(id = id,  library = request.user.subscriber.library_id, is_active= True).first()
            if media is not None:
                serializer = LearningMaterialMediaSerializer(media, context = {'request':request}).data
                return Response({'results': serializer}, status=status.HTTP_200_OK)
            return Response({'success':False}, status= status.HTTP_200_OK)
        else:
            return Response({'error': 'no permission'}, status=status.HTTP_200_OK)

# download

class MediaDownloadView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, id):
        if request.user.is_subscriber():
            media = Media.objects.filter(id= id, library_id = request.user.subscriber.library_id, is_active= True).first()
            subscriber_media = SubscriberMedia.objects.filter(media_id= id, subscriber_id = request.user.id).first()

            if media is None:
                return Response({'success': False, 'error': 'library does not have this media'}, status=status.HTTP_200_OK)
            
            if subscriber_media is not None:
                return Response({'success': False, 'error': 'you have downloaded this media'}, status=status.HTTP_200_OK)

            media.number_of_download += 1 
            media.save()

            subscriber = SubscriberMedia.objects.create(
                media_id = media.id,
                subscriber_id = request.user.id
            )
            subscriber.save()

            transaction = SubscriberMediaTransaction.objects.create(
                action = SubscriberMediaAction.DOWNLOADED,
                media_id = media.id,
                subscriber_id = request.user.id
            )
            transaction.save()

            return Response({'success': True}, status= status.HTTP_200_OK)

        return Response({'success': False, 'error': 'no permission'}, status=status.HTTP_200_OK)

class MediaReturnView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, id):
        if request.user.is_subscriber():
            media = SubscriberMedia.objects.filter(media_id= id, subscriber_id = request.user.id).first()

            if media is None:
                return Response({'success': False, 'error': 'you have not downloaded this media'}, status=status.HTTP_200_OK)

            media.delete()
            transaction = SubscriberMediaTransaction.objects.create(
                action = SubscriberMediaAction.RETURN,
                media_id = id,
                subscriber_id = request.user.id
            )
            transaction.save()

            return Response({'success': True}, status=status.HTTP_200_OK)
        
        return Response({'success':False, 'error': 'no permission'}, status=status.HTTP_200_OK)

class LearningMaterialDownloadedView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = LearningMaterialMediaSerializer
    def get(self, request):
        if self.request.user.is_subscriber():
            media = Media.objects.filter(learning_material_subscriber_medias__subscriber_id = self.request.user.id)
            serializer = LearningMaterialMediaSerializer(media, context={'request':request}, many= True).data
            return Response({'results': serializer}, status=status.HTTP_200_OK)
        return Response({'success': False, 'error': 'no permission'}, status=status.HTTP_200_OK)

class LearningMaterialDeleteView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = MediaSerializer

    def get_queryset(self):
        return Media.objects.filter(library = self.request.user.librarian.library_id)

    def perform_destroy(self, instance):
        path = os.path.join(settings.MEDIA_ROOT, str(instance.url))
        os.remove(path)

        SubscriberMediaTransaction.objects.filter(media = instance).delete()
        SubscriberMedia.objects.filter(media = instance).delete()
        MediaImage.objects.filter(media = instance).delete()
        instance.delete()
        