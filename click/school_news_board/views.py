import json
import sys
import os
import io
from django.conf import settings
from django.utils import timezone
from django.conf import settings

from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework import generics, renderers, viewsets, status, mixins, views, serializers, parsers
from click.school_news_board.models import SchoolNewsBoard
from click.school_news_board.serializers import SchoolNewsBoardSerializer

from click.users.serializers import UserSerializer
from django_filters import rest_framework as filters
from click.users.models import Librarian, UserType, User
from click.notification.models import NotificationStatus, NotificationType, MessageNotification, UploadType, ConfirmUpload
from click.notification.serializers import NotificationReceiverSerializer, NotificationProducerSerializer

# Create your views here.

class SchoolNewsBoardFilter(filters.FilterSet):
    title = filters.CharFilter(field_name="title", lookup_expr='icontains')

    class Meta:
        model = SchoolNewsBoard
        fields = ['title']

class SchoolNewsBoardView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]
    filterset_class = SchoolNewsBoardFilter
    ordering_fields = ['title']
    serializer_class = SchoolNewsBoardSerializer

    
    def get_queryset(self):
        if self.request.user.is_librarian():
            return SchoolNewsBoard.objects.filter(created_by = self.request.user).order_by('-id')
        elif self.request.user.is_subscriber():
            return SchoolNewsBoard.objects.filter(created_by__librarian__library_id= self.request.user.subscriber.library_id, is_active= True).order_by('-id')
        
    def post(self, request):
        data = request.data.dict()
        if request.user.is_librarian():
            serializer = SchoolNewsBoardSerializer(data={
                **data,
                'created_by': request.user.id,
                'updated_by': request.user.id
            })
            serializer.is_valid(raise_exception=True)
            school_news_board = serializer.save()
            
            producer = NotificationProducerSerializer(data={
                'user': request.user.id
            })
            producer.is_valid(raise_exception=True)
            noti_producer = producer.save()

            receiver = NotificationReceiverSerializer(data={
                    'producer': noti_producer.id,
                    'notification_type': NotificationType.CONFIRM_UPLOAD,
                    'message': MessageNotification.LOG_UPLOAD_SCHOOL_NEWS_BOARD,
                    'user': User.objects.filter(user_type= UserType.ADMIN).first().id,
                })
            receiver.is_valid(raise_exception= True)
            noti_receiver = receiver.save()

            confirm = ConfirmUpload.objects.create( 
                receiver = noti_receiver,
                upload_type = UploadType.SCHOOL_NEWS_BOARD,
                name = school_news_board.title
            )
            confirm.save()
            return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)                                                                              
        return Response({'success': False}, status=status.HTTP_400_BAD_REQUEST)
        

class SchoolNewsBoardDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]
    serializer_class= SchoolNewsBoardSerializer

    def get_queryset(self):
        if self.request.user.is_librarian():
            return SchoolNewsBoard.objects.filter(created_by = self.request.user).order_by('-id')
        elif self.request.user.is_subscriber():
            return SchoolNewsBoard.objects.filter(created_by__librarian__library_id= self.request.user.subscriber.library_id, is_active= True).order_by('-id')

    def patch(self, request, *args, **kwargs):
        data = request.data.dict()
        snb = self.get_object()
        if request.user.is_librarian():
            serializer = SchoolNewsBoardSerializer(snb, data={**data, 'updated_by': request.user.id}, partial= True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'Success': True}, status= status.HTTP_200_OK)
        return Response({'success': False}, status=status.HTTP_400_BAD_REQUEST)

    def perform_destroy(self, instance):
        instance.is_active = not instance.is_active
        instance.save()

class SchoolNewsBoardDeleteView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class= SchoolNewsBoardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return SchoolNewsBoard.objects.filter(created_by = self.request.user)

    def perform_destroy(self, instance):
        path = os.path.join(settings.MEDIA_ROOT, str(instance.photo))
        os.remove(path)
        instance.delete()