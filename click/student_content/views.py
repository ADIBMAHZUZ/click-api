import json
import sys
import io
import os

from django.utils import timezone
from django.db.models import Q
from django.conf import settings

from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, JSONParser
from rest_framework.response import Response
from rest_framework import generics, renderers, permissions, viewsets, status, mixins, views, serializers, parsers

from click.student_content.models import StudentContent, StudentContentStatus
from click.student_content.serializers import StudentContentSerializer
from django_filters import rest_framework as filters

from click.users.serializers import UserSerializer
from click.users.models import Teacher, Librarian, UserType
from click.notification.serializers import NotificationProducerSerializer, NotificationReceiverSerializer
from click.notification.models import NotificationStatus, NotificationType, UploadType, ConfirmUpload, MessageNotification

from django.contrib.auth import get_user_model
User = get_user_model()


class StudentContentFilter(filters.FilterSet):
    title = filters.CharFilter(field_name="title", lookup_expr='icontains')

    class Meta:
        model = StudentContent
        fields = ['title', 'status']

# Web
class StudentContentView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]
    filterset_class = StudentContentFilter
    ordering_fields = ['title']
    serializer_class = StudentContentSerializer

    def get_queryset(self):
        queryset = StudentContent.objects.all()
        
        if self.request.user.is_subscriber():
            queryset = StudentContent.objects.filter(created_by= self.request.user.id)
        
        elif self.request.user.is_librarian():
            queryset = StudentContent.objects.filter(Q(created_by__librarian__library_id = self.request.user.librarian.library_id) |\
                 Q(created_by__subscriber__library_id = self.request.user.librarian.library_id))
        
        return queryset.order_by('-id')

    def post(self, request):
        data = request.data.dict()
        if request.user.is_subscriber():
            serializer = StudentContentSerializer(data={
                **data,
                'status': StudentContentStatus.DRAFT,
                'created_by': request.user.id,
                'updated_by': request.user.id
            })
        elif request.user.is_librarian():
            serializer = StudentContentSerializer(data={
                **data,
                'created_by': request.user.id,
                'updated_by': request.user.id
            })
        
        serializer.is_valid(raise_exception=True)
        student_content = serializer.save()

        if request.user.is_subscriber():
            return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)

        producer = NotificationProducerSerializer(data={
            'user': request.user.id
        })
        producer.is_valid(raise_exception=True)
        noti_producer = producer.save()

        receiver = NotificationReceiverSerializer(data={
                'producer': noti_producer.id,
                'notification_type': NotificationType.CONFIRM_UPLOAD,
                'message': MessageNotification.LOG_UPLOAD_STUDENT_CONTENT,
                'user': User.objects.filter(user_type= UserType.ADMIN).first().id,
            })
        receiver.is_valid(raise_exception= True)
        noti_receiver = receiver.save()

        confirm = ConfirmUpload.objects.create(
            receiver = noti_receiver,
            upload_type = UploadType.STUDENT_CONTENT,
            name = student_content.title
        )
        confirm.save()    
        return Response({'success': True, 'data': serializer.data}, status=status.HTTP_201_CREATED)

class StudentContentDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]
    serializer_class= StudentContentSerializer

    def get_queryset(self):
        queryset = StudentContent.objects.all()
        
        if self.request.user.is_subscriber():
            queryset = StudentContent.objects.filter(created_by= self.request.user.id)
        
        elif self.request.user.is_librarian():
            queryset = StudentContent.objects.filter(Q(created_by__librarian__library_id = self.request.user.librarian.library_id) |\
                 Q(created_by__subscriber__library_id = self.request.user.librarian.library_id))
        
        return queryset

    def patch(self, request, *args, **kwargs):
        sc = self.get_object()
        data = request.data.dict()
        
        if self.request.user.is_subscriber():
            serializer = StudentContentSerializer(sc, data={**data, 'status': sc.status,'updated_by': request.user.id}, partial= True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'success': True})

        if self.request.user.is_librarian():
            current_status = sc.status
            update_status = data.get('status')
            serializer = StudentContentSerializer(sc, data={**data, 'updated_by': request.user.id}, partial= True)
            serializer.is_valid(raise_exception=True)
            student_content = serializer.save()
            
            if current_status == StudentContentStatus.DRAFT and update_status == StudentContentStatus.PUBLISH:
                producer = NotificationProducerSerializer(data={
                    'user': request.user.id
                })
                producer.is_valid(raise_exception=True)
                noti_producer = producer.save()

                receiver = NotificationReceiverSerializer(data={
                        'producer': noti_producer.id,
                        'notification_type': NotificationType.CONFIRM_UPLOAD,
                        'message': MessageNotification.LOG_UPLOAD_STUDENT_CONTENT,
                        'user': User.objects.filter(user_type= UserType.ADMIN).first().id,
                    })
                receiver.is_valid(raise_exception= True)
                noti_receiver = receiver.save()

                confirm = ConfirmUpload.objects.create(
                    receiver = noti_receiver,
                    upload_type = UploadType.STUDENT_CONTENT,
                    name = student_content.title
                )
                confirm.save()
            return Response({'success': True})
        return Response({'success': False, 'error': 'No permission'}, status=status.HTTP_400_BAD_REQUEST)

        

    def perform_destroy(self, instance):
        if self.request.user.is_librarian():
            instance.is_active = not instance.is_active
            instance.save()

class DeleteStudentContentView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class= StudentContentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = StudentContent.objects.all()
        if self.request.user.is_subscriber():
            queryset = StudentContent.objects.filter(created_by= self.request.user.id, is_active= True)
        
        elif self.request.user.is_librarian():
            queryset = StudentContent.objects.filter(Q(created_by__librarian__library_id = self.request.user.librarian.library_id) |\
                 Q(created_by__subscriber__library_id = self.request.user.librarian.library_id))
        return queryset


    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        if request.user.is_subscriber():
            if obj.status == StudentContentStatus.DRAFT:
                path = os.path.join(settings.MEDIA_ROOT, str(obj.photo))
                os.remove(path)
                obj.delete()
                return Response({'success':True}, status=status.HTTP_200_OK)
        elif request.user.is_librarian():
            path = os.path.join(settings.MEDIA_ROOT, str(obj.photo))
            os.remove(path)
            obj.delete()
            return Response({'success':True}, status=status.HTTP_200_OK)
        return Response({'success':False, 'error':'No permission'}, status=status.HTTP_400_BAD_REQUEST)        

# Mobile
class StudentContentMobileView(generics.ListAPIView):
    serializer_class= StudentContentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return StudentContent.objects.filter(Q(created_by__librarian__library_id = self.request.user.subscriber.library_id, is_active= True, status= StudentContentStatus.PUBLISH) |\
            Q(created_by__subscriber__library_id = self.request.user.subscriber.library_id, is_active= True, status= StudentContentStatus.PUBLISH)).order_by('-id')

class StudentContentMobileDetailView(generics.RetrieveAPIView):
    serializer_class= StudentContentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return StudentContent.objects.filter(Q(created_by__librarian__library_id = self.request.user.subscriber.library_id, is_active= True, status= StudentContentStatus.PUBLISH) |\
            Q(created_by__subscriber__library_id = self.request.user.subscriber.library_id, is_active= True, status= StudentContentStatus.PUBLISH))