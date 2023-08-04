import json
import sys
import os
import io

from django.conf import settings
from django.utils import timezone

from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework import generics, renderers, permissions, viewsets, status, mixins, views, serializers, parsers

from click.school_history.models import SchoolHistory
from click.school_history.serializers import SchoolHistorySerializer

from click.users.serializers import UserSerializer
from django_filters import rest_framework as filters
from click.users.models import Librarian, User, UserType
from click.notification.models import NotificationStatus, NotificationType, ConfirmUpload, MessageNotification, UploadType
from click.notification.serializers import NotificationProducerSerializer, NotificationReceiverSerializer

from django.contrib.auth import get_user_model
User = get_user_model()

# Create your views here.

class SchoolHistoryFilter(filters.FilterSet):
    title = filters.CharFilter(field_name="title", lookup_expr='icontains')

    class Meta:
        model = SchoolHistory
        fields = ['title']

class SchoolHistoryView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]
    filterset_class = SchoolHistoryFilter
    ordering_fields = ['title']
    serializer_class = SchoolHistorySerializer

    def get_queryset(self):
        if self.request.user.is_librarian():
            return SchoolHistory.objects.filter(created_by = self.request.user)

        elif self.request.user.is_subscriber():
            return SchoolHistory.objects.filter(created_by__librarian__library = self.request.user.subscriber.library_id, is_active= True)

    def post(self, request):
        data = request.data.dict()
        if request.user.is_librarian():
            serializer = SchoolHistorySerializer(data={
                **data,
                'created_by': request.user.id,
                'updated_by': request.user.id
            })
            serializer.is_valid(raise_exception=True)
            school_history = serializer.save()

            producer = NotificationProducerSerializer(data={
                'user': request.user.id
            })
            producer.is_valid(raise_exception=True)
            noti_producer = producer.save()

            receiver = NotificationReceiverSerializer(data={
                    'producer': noti_producer.id,
                    'notification_type': NotificationType.CONFIRM_UPLOAD,
                    'message': MessageNotification.LOG_UPLOAD_SCHOOL_HISTORY,
                    'user': User.objects.filter(user_type= UserType.ADMIN).first().id,
                })
            receiver.is_valid(raise_exception= True)
            noti_receiver = receiver.save()

            confirm = ConfirmUpload.objects.create( 
                receiver = noti_receiver,
                upload_type = UploadType.SCHOOL_HISTORY,
                name = school_history.title
            )
            confirm.save()
            return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)
        return Response({'success': False}, status=status.HTTP_400_BAD_REQUEST)
        

class SchoolHistoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]
    serializer_class= SchoolHistorySerializer

    def get_queryset(self):
        if self.request.user.is_librarian():
            return SchoolHistory.objects.filter(created_by = self.request.user)

        elif self.request.user.is_subscriber():
            return SchoolHistory.objects.filter(created_by__librarian__library = self.request.user.subscriber.library_id, is_active= True)


    def patch(self, request, *args, **kwargs):
        sh = self.get_object()
        data = request.data.dict()
        if request.user.is_librarian():
            serializer = SchoolHistorySerializer(sh, data={**data, 'updated_by': request.user.id}, partial= True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'Success': True}, status= status.HTTP_200_OK)
        return Response({'success': False}, status=status.HTTP_400_BAD_REQUEST)

    def perform_destroy(self, instance):
        instance.is_active = not instance.is_active
        instance.save()

class SchoolHistoryDeleteView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class= SchoolHistorySerializer

    def get_queryset(self):
        return SchoolHistory.objects.filter(created_by = self.request.user)

    def perform_destroy(self, instance):
        path = os.path.join(settings.MEDIA_ROOT, str(instance.photo))
        os.remove(path)
        instance.delete()