import json
import sys
import os
import io
import random
import string
import re
from pathlib import Path
from django.conf import settings
from django.contrib.auth import authenticate
from django.utils import timezone
from django.core.mail import send_mail, send_mass_mail
from django.core.mail import EmailMultiAlternatives, get_connection
from django.db import transaction
from django.http import QueryDict
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth.hashers import make_password
from django.db.models import Q, Count

from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import generics, renderers, permissions, viewsets, status, mixins, views, serializers, parsers, pagination
from click.media.models import LibraryMedia, Media

from click.users.models import Token, ForgotPasswordToken, Library, UserType, Librarian, Teacher, Admin, Publisher, Subscriber, UsersActivity, UserAction, Device
from click.users.serializers import *
from click.users.tasks import create_subscribers, create_teachers

from click.teacher_notes.models import NotesDownloaded, TeacherNotesAction, TeacherNotes, FileType, TeacherNotesDownloaded, TeacherNotesTransaction
from click.teacher_notes.serializers import TeacherNotesCreateSerializer

from django.contrib.auth import get_user_model

User = get_user_model()

def checkUsername(str):
    regex = ("^(?=.*[a-z])(?=." + "*[A-Z])(?=.*\\d)" + "(?=.*[-+_!@#$%^&*., ?]).+$")


    if (re.search(re.compile(regex), str)):
        return True
    else:
        return False


# Create your views here.
class ForgotPasswordView(views.APIView):
    """
    Forgot password.
    """

    class ForgotPasswordDataSerializer(serializers.Serializer):
        username = serializers.CharField()
        email = serializers.EmailField()

    serializer_class = ForgotPasswordDataSerializer

    def post(self, request, format='json'):
        username = request.data.get("username")
        email = request.data.get("email")

        if username is None:
            return Response({'error': 'Username is required', 'success': False})

        if email is None:
            return Response({'error': 'Email is required', 'success': False})

        try:
            user = User.objects.get(username=username, email=email)
        except User.DoesNotExist:
            user = None

        if not user:
            return Response({'error': 'Email is not exists', 'success': False})

        ForgotPasswordToken.objects.filter(user=user).delete()
        token = ForgotPasswordToken.objects.create(user=user)

        

        if user.is_subscriber():
            message = f"""
            Create New Password!
            Your username: {user.username}
            Your token: {token}
            """
        else:
            link=request.build_absolute_uri("/api/auth/create-new-password/?token="+str(token))
            message = f"""<h2>Create New Password!</h2>
            <p>Your username: {user.username}</p>
            <p>Click here {link} to create new password.</p>"""

        send_mail("CLICk - Create New Password", message, "CLICk <no-reply@click.com>", [user.email], html_message=message)

        return Response({'success': True,})


class CheckForgotPasswordTokenView(views.APIView):
    """
    Check forgot password token.
    """

    class CheckForgotPasswordTokenDataSerializer(serializers.Serializer):
        token = serializers.CharField()

    serializer_class = CheckForgotPasswordTokenDataSerializer

    def post(self, request, format='json'):
        token = request.data.get("token")

        if token is None:
            return Response({'error': 'Please provide token', 'success': False})

        try:
            instance = ForgotPasswordToken.objects.get(pk=token)
        except ForgotPasswordToken.DoesNotExist:
            instance = None

        if not instance:
            return Response({'error': 'Token is not exists', 'success': False})

        return Response({'success': True})


class CreateNewPasswordView(views.APIView):
    """
    Create new password.
    """

    class CheckForgotPasswordTokenDataSerializer(serializers.Serializer):
        token = serializers.CharField()
        new_password = serializers.CharField()
        confirm_password = serializers.CharField()

    serializer_class = CheckForgotPasswordTokenDataSerializer

    def post(self, request, format='json'):
        token = request.data.get("token")
        new_password = request.data.get("new_password")
        confirm_password = request.data.get("confirm_password")

        if token is None:
            return Response({'error': 'Please provide token', 'success': False})

        if new_password is None:
            return Response({'error': 'Please provide new password', 'success': False})

        if new_password != confirm_password:
            return Response({'error': 'New password does not match', 'success': False})

        if len(new_password) < 6:
            return Response({'error': 'New password must be at least 6 characters'})

        try:
            instance = ForgotPasswordToken.objects.get(pk=token)
        except ForgotPasswordToken.DoesNotExist:
            instance = None

        if not instance:
            return Response({'error': 'Token is not valid', 'success': False})

        user = User.objects.get(pk=instance.user_id)

        if not user:
            return Response({'error': 'User is not exists', 'success': False})

        user.set_password(new_password)
        user.save()
        instance.delete()

        return Response({'success': True})


class LoginView(views.APIView):
    """
    Login.
    """

    class LoginDataSerializer(serializers.Serializer):
        username = serializers.CharField()
        password = serializers.CharField(style={'input_type': 'password'})

    serializer_class = LoginDataSerializer

    def post(self, request, format='json'):

        username = request.data.get("username")
        password = request.data.get("password")
        device = request.data.get('device')

        if username is None or password is None:
            return Response({'error': 'Wrong username and password', 'code': 'CLICk400', 'success': False})

        user = authenticate(username=username, password=password)

        user_object = User.objects.filter(username=username).first()
        if user_object != None:
            if user_object.is_active == False:
                return Response({'error': 'User is inactive', 'code': 'CLICk401', 'success': False})

        if not user:
            return Response({'error': 'Wrong username and password', 'code': 'CLICk400', 'success': False})

        if user.user_type == UserType.TEACHER:
            library = Library.objects.filter(id=user.teacher.library_id).first().is_active
            if library == False:
                return Response({'error': 'Your library is temporarily locked', 'code': 'CLICk404', 'success': False})

        if user.user_type == UserType.SUBSCRIBER:

            library = Library.objects.filter(id=user.subscriber.library_id).first().is_active
            if library == False:
                return Response({'error': 'Your library is temporarily locked', 'code': 'CLICk403', 'success': False})

            if device is None:
                return Response({'error': 'Unable to identify the device', 'code': 'CLICk405', 'success': False})

            if device == Device.MOBILE:
                number_of_tokens = Token.objects.filter(user=user, device=Device.MOBILE).count()
                if number_of_tokens >= user.subscriber.max_device:
                    return Response({'error': 'This account is logged more than ' + str(user.subscriber.max_device) + ' different devices', 'code': 'CLICk402', 'success': False})

            library = LibrarySerializer(user.subscriber.library, context={'request': request})
            librarian = Librarian.objects.get(library_id=user.subscriber.library.id)
            userLibrarianSerializer = UserSerializer(librarian.user, context={'request': request}).data
            userSerializer = UserSerializer(user, context={'request': request}).data

            response = {
                'max_download': user.subscriber.max_download,
                'max_borrow_duration': user.subscriber.max_borrow_duration,
                'logo': userSerializer['logo'],
                'library': {'name': librarian.user.name, 'logo': userLibrarianSerializer['logo'], 'short_name': librarian.user.short_name, **library.data,},
            }

        if user.user_type != UserType.SUBSCRIBER:
            response = {
                'permissions': user.get_all_permissions(),
            }

        token = Token.objects.create(user=user, device=device)

        response = {
            **response,
            'token': token.key,
            'success': True,
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'name': user.name,
            'short_name': user.short_name,
            'user_type': user.user_type,
        }

        trackingAction = UsersActivity.objects.create(user=user, action=UserAction.LOGIN)
        trackingAction.save()

        return Response(response)


class LogoutView(views.APIView):
    """
    Logout.
    """

    class LogoutDataSerializer(serializers.Serializer):
        token = serializers.CharField()

    serializer_class = LogoutDataSerializer

    def post(self, request, format='json'):
        token = request.data.get("token")

        if token is None:
            return Response({'error': 'Please provide token', 'success': False})

        token_object = Token.objects.filter(pk=token).first()

        if token_object is None:
            return Response({'error': 'Invalid Credentials', 'success': False})

        tracking_action = UsersActivity.objects.create(user_id=token_object.user.id, action=UserAction.LOGOUT)
        tracking_action.save()

        token_object.delete()

        return Response({'success': True})


class ActivateAccountView(views.APIView):
    """
    Activate Account.
    """

    def post(self, request, format='json'):
        token = request.data.get("token")

        if token is None:
            return Response({'error': 'Please provide token', 'success': False})

        try:
            user = User.objects.get(activate_token=token)
        except User.DoesNotExist:
            user = None

        if not user:
            return Response({'error': 'Token is not exists', 'success': False})

        if user.activate_time:
            return Response({'error': 'User have already activated', 'success': False})

        user.activate_time = timezone.now()
        user.save()

        return Response({'success': True})


class ProfileView(views.APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, format=None):
        user = UserSerializer(request.user, context={'request': request}).data
        if request.user.is_admin():
            data = {**user}

        elif request.user.is_publisher():
            publishers = PublisherSerializer(Publisher.objects.get(user_id=request.user.id), context={'request': request}).data
            data = {**user, **publishers}

        elif request.user.is_librarian():
            librarian = LibrarianSerializer(Librarian.objects.get(user_id=request.user.id), context={'request': request}).data
            lib_id = Librarian.objects.get(user_id=request.user.id).library_id
            library = LibrarySerializer(Library.objects.get(id=lib_id), context={'request': request}).data
            data = {**user, **librarian, **library, 'id': request.user.id}

        elif request.user.is_subscriber():
            subscriber = SubscriberSerializer(Subscriber.objects.get(user_id=request.user.id), context={'request': request}).data
            lib_id = Subscriber.objects.get(user_id=request.user.id).library_id
            library = LibrarySerializer(Library.objects.get(id=lib_id), context={'request': request}).data
            data = {**user, **subscriber, **library, 'id': request.user.id}

        elif request.user.is_teacher():
            teacher = TeacherSerializer(Teacher.objects.get(user_id=request.user.id), context={'request': request}).data
            data = {**user, **teacher}

        return Response(data)

    def patch(self, request, *args, **kwargs):

        data = request.data.dict()
        serializer = UserSerializer(request.user, data={**data, 'password': request.user.password, 'user_type': request.user.user_type, 'is_active': request.user.is_active})
        if request.user.is_admin():
            pass

        elif request.user.is_publisher():
            publishers = PublisherSerializer(request.user, data={**data, 'user_id': request.user.id})
            publishers.is_valid(raise_exception=True)

        elif request.user.is_librarian():
            librarian = LibrarianSerializer(Librarian.objects.get(user_id=request.user.id), data={**data, 'user_id': request.user.id})
            library = LibrarySerializer(Library.objects.get(id=request.user.librarian.library.id), data={**data})
            librarian.is_valid(raise_exception=True)
            librarian.save()
            library.is_valid(raise_exception=True)
            library.save()

        elif request.user.is_teacher():
            teacher = TeacherSerializer(Teacher.objects.get(user_id=request.user.id), data={**data, 'user_id': request.user.id})
            teacher.is_valid(raise_exception=True)
            teacher.save()

        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'success': True}, status=status.HTTP_200_OK)


class ChangePasswordView(views.APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, format=None):

        password = request.data.get('password', '')
        new_password = request.data.get('new_password', '')
        confirm_password = request.data.get('confirm_password', '')

        if new_password != confirm_password:
            return Response({'error': 'New password and confirm password are not match', 'success': False})

        if len(new_password) < 6:
            return Response({'error': 'New password must be at least 6 characters', 'success': False})

        user = authenticate(username=request.user.username, password=password)

        if not user:
            return Response({'error': 'Current Password is incorrect', 'success': False})

        user.set_password(new_password)
        user.save()

        return Response({'success': True})


class LibrarianView(generics.ListAPIView):

    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]
    serializer_class = UserLibrarySerializer
    # filterset_fields = ['username', 'email']
    search_fields = ['username', 'email', 'name', 'short_name', 'phone']
    ordering_fields = ['username', 'email', 'name', 'short_name', 'phone']
    filter_backends = (SearchFilter, OrderingFilter)

    def get_queryset(self):
        get_id = self.request.query_params.get('library')
        if get_id is None:
            return User.objects.filter(user_type=UserType.LIBRARIAN).order_by('-id')
        return User.objects.filter(user_type=UserType.LIBRARIAN, librarian__library_id=get_id).order_by('-id')

    def post(self, request):
        data = request.data.dict()

        username=data.get('username')

        if not checkUsername(username):
            return Response({'success': False, 'message': "Must contain at least 1 uppercase letter, 1 lowercase letter, 1 special character and 1 digit in Username."})

        library = Library.objects.create(is_active=data.get('is_active'), max_subscribers=data.get('max_subscribers'))
        library.save()

        userSerializer = UserSerializer(data={**data, 'user_type': UserType.LIBRARIAN,})
        userSerializer.is_valid(raise_exception=True)
        user = userSerializer.save()
        user.set_password(data.get('password'))
        user.save()

        librarian = Librarian.objects.create(user_id=user.id, library_id=library.id,)
        librarian.save()

        return Response({'success': True, 'data': userSerializer.data}, status=status.HTTP_201_CREATED)


class LibraryView(views.APIView):
    def get(self, request):

        users = User.objects.filter(is_active=True, user_type=UserType.LIBRARIAN).select_related('librarian', 'librarian__library')

        libraries = []

        for user in users:
            libraries.append({'id': user.librarian.library.id, 'name': user.name})

        return Response({'results': libraries})
    def post(self, request):
        name=request.data.get('name')
        if name:
            users = User.objects.filter(is_active=True, user_type=UserType.LIBRARIAN,name__icontains=name).select_related('librarian', 'librarian__library')
        else:
            users = User.objects.filter(is_active=True, user_type=UserType.LIBRARIAN).select_related('librarian', 'librarian__library')

        libraries = []

        for user in users:
            libraries.append({'id': user.librarian.library.id, 'name': user.name})

        return Response({'results': libraries})


class LibrarianDetailView(generics.RetrieveDestroyAPIView):

    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]
    serializer_class = UserLibrarySerializer

    def get_queryset(self):
        return User.objects.filter(user_type=UserType.LIBRARIAN)

    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        data = request.data.dict()
        new_max_subscribers = data.get('max_subscribers')
        librarian = Librarian.objects.filter(user_id=user.id).first().library_id
        number_of_subscribers = Subscriber.objects.filter(library_id=librarian).count()

        if int(new_max_subscribers) >= number_of_subscribers:
            serializer = UserSerializer(user, data=data, partial=True)
            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            if data.get('password', '') != '':
                user.set_password(data.get('password'))
                user.save()

            if user.is_active == False:
                Token.objects.filter(user_id=user.id).delete()

                subscribers = Subscriber.objects.filter(library_id=user.id)

                for subscriber in subscribers:
                    Token.objects.filter(user_id=subscriber.user_id).delete()

            librarian = Librarian.objects.filter(user_id=user.id).first().library_id
            library = Library.objects.filter(id=librarian).first()
            library.max_subscribers = data.get('max_subscribers')
            library.save()

            return Response({'success': True}, status=status.HTTP_200_OK)
        else:
            return Response({'success': False, 'error': 'Max subscribers can not set smaller than number of subcribers in the system'}, status=status.HTTP_400_BAD_REQUEST)

    def perform_destroy(self, instance):
        instance.is_active = not instance.is_active
        instance.save()

        library = instance.librarian.library
        library.is_active = instance.is_active
        library.save()

        if library.is_active == False:
            Token.objects.filter(user_id=instance.id).delete()

            subscribers = Subscriber.objects.filter(library_id=library.id)

            for subscriber in subscribers:
                Token.objects.filter(user_id=subscriber.user_id).delete()


class TeacherView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]
    serializer_class = UserTeacherSerializer
    search_fields = ['name']
    ordering_fields = ['username', 'email', 'name', 'short_name', 'phone']
    filter_backends = (SearchFilter, OrderingFilter)

    def get_queryset(self):
        get_id = self.request.query_params.get('library')
        if self.request.user.is_admin():
            if get_id is None:
                return User.objects.filter(user_type=UserType.TEACHER).order_by('-id')
            return User.objects.filter(user_type=UserType.TEACHER, teacher__library_id=get_id).order_by('-id')
        elif self.request.user.is_librarian():
            return User.objects.filter(user_type=UserType.TEACHER, teacher__library_id=self.request.user.librarian.library_id).order_by('-id')
        elif self.request.user.is_subscriber():
            return (
                User.objects.annotate(teacher_count=Count('teacher_notes__id'))
                .filter(user_type=UserType.TEACHER, teacher__library_id=self.request.user.subscriber.library_id, is_active=True, teacher_count__gt=1)
                .order_by('-id')
            )

    def post(self, request):
        data = request.data.dict()

        username=data.get('username')
        storage=float(data.get('storage'))

        if not checkUsername(username):
            return Response({'success': False, 'message': "Must contain at least 1 uppercase letter, 1 lowercase letter, 1 special character and 1 digit in Username."})

        if request.user.is_admin():
            library_id=data.get('library_id')
            library=Librarian.objects.filter(library_id=library_id).first()
            if not library:
                return Response({'success': False, 'message': "Library does not exist."})

        elif request.user.is_librarian():

            library=request.user.librarian

        media =  MediaLibrary.objects.filter(library_id = library.library_id).aggregate(size = Sum('file_size'))
        teacher=Teacher.objects.filter(library_id = library.library_id).aggregate(storage = Sum('storage'))
        current_storage=0
        if media['size'] is not None :
            current_storage += round(int(media['size']) / (math.pow(1024, 3)), 2)
        if teacher['storage'] is not None :
            current_storage += round(teacher['storage'],2)

        if storage>(library.storage-current_storage):
            return Response({'success': False, 'message': "Storage is higher than library's storage"})

        userSerializer = UserSerializer(data={**data, 'user_type': UserType.TEACHER})

        userSerializer.is_valid(raise_exception=True)
        user = userSerializer.save()
        user.set_password(data.get('password'))
        user.save()

        teacher = Teacher.objects.create(user_id=user.id, subject=data.get('subject'), library_id=request.user.librarian.library_id,storage=storage)
        teacher.save()

        teacher_notes = TeacherNotesCreateSerializer(data={'name': user.id, 'file_type': FileType.FOLDER, 'url': os.path.join(settings.NOTES, str(user.id)), 'teacher': user.id})
        teacher_notes.is_valid(raise_exception=True)
        teacher_notes.save()

        Path(os.path.join(settings.MEDIA_ROOT, settings.NOTES, str(user.id))).mkdir(parents=True, exist_ok=True)
        return Response({'success': True, 'data': userSerializer.data}, status=status.HTTP_201_CREATED)


class TeacherDetailView(generics.RetrieveDestroyAPIView):

    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]
    serializer_class = UserTeacherSerializer

    def get_queryset(self):
        if self.request.user.is_admin():
            query_set = User.objects.filter(user_type=UserType.TEACHER).order_by('-id')
        elif self.request.user.is_librarian():
            teacher = Teacher.objects.filter(library_id=self.request.user.librarian.library_id)
            list_id = []
            for tea in teacher:
                list_id.append(tea.user_id)
            query_set = User.objects.filter(id__in=list_id)
        elif self.request.user.is_subscriber():
            teacher = Teacher.objects.filter(library_id=self.request.user.subscriber.library_id)
            list_id = []
            for tea in teacher:
                list_id.append(tea.user_id)
            query_set = User.objects.filter(id__in=list_id, is_active=True)
        return query_set

    def patch(self, request, *args, **kwargs):

        data = request.data.dict()
        storage=float(data.get('storage'))
        user = self.get_object()

        serializer = UserSerializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if data.get('password', '') != '':
            user.set_password(data.get('password'))
            user.save()

        if user.is_active == False:
            Token.objects.filter(user_id=user.id).delete()

        teacher = Teacher.objects.filter(user_id=user.id).first()
        teacher.subject = data.get('subject')

        if teacher.storage<storage:
            library=request.user.librarian
            
            media =  MediaLibrary.objects.filter(library_id = library.library_id).aggregate(size = Sum('file_size'))
            teacher_storage=Teacher.objects.filter(library_id = library.library_id).aggregate(storage = Sum('storage'))
            current_storage=0
            if media['size'] is not None :
                current_storage += round(int(media['size']) / (math.pow(1024, 3)), 2)
            if teacher_storage['storage'] is not None :
                current_storage += round(teacher_storage['storage'],2)

            if (storage-teacher.storage)>(library.storage-current_storage):
                return Response({'success': False, 'message': "Storage is higher than library's storage"})

        teacher.storage=storage
        teacher.save()

        return Response({'success': True}, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        instance.is_active = not instance.is_active
        instance.save()

        if instance.is_active == False:
            note_id = os.path.join(settings.TEACHER_NOTES, 'teacher_notes', str(instance.id))
            NotesDownloaded.objects.filter(url__icontains=note_id).delete()
            TeacherNotesAction.objects.filter(url__icontains=note_id).delete()

            # news
            TeacherNotesDownloaded.objects.filter(note__teacher_id=instance.id).delete()
            TeacherNotesTransaction.objects.filter(note__teacher_id=instance.id).delete()
            Token.objects.filter(user_id=instance.id).delete()


class SubscriberView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]
    search_fields = ['username', 'email', 'name', 'short_name', 'phone']
    ordering_fields = ['username', 'email', 'name', 'short_name', 'phone']
    filter_backends = (SearchFilter, OrderingFilter)
    serializer_class = UserSubscriberSerializer

    def get_queryset(self):
        get_id = self.request.query_params.get('library')
        if self.request.user.is_admin():
            if get_id is None:
                return User.objects.filter(user_type=UserType.SUBSCRIBER).order_by('-id')
            return User.objects.filter(user_type=UserType.SUBSCRIBER, subscriber__library_id=get_id).order_by('-id')
        elif self.request.user.is_librarian():
            return User.objects.filter(subscriber__library=self.request.user.librarian.library_id).order_by('-id')

    def post(self, request):

        if request.user.is_librarian():
            data = request.data.dict()
            username=data.get('username')
            if not checkUsername(username):
                return Response({'success': False, 'message': "Must contain at least 1 uppercase letter, 1 lowercase letter, 1 special character and 1 digit in Username."})

            number_subscriber = Subscriber.objects.filter(library_id=request.user.librarian.library_id).count()
            number_subscriber_library = Library.objects.filter(id=request.user.librarian.library_id).first().max_subscribers
            if number_subscriber < number_subscriber_library:
                userSerializer = UserSerializer(data={**data, 'user_type': UserType.SUBSCRIBER})
                userSerializer.is_valid(raise_exception=True)
                user = userSerializer.save()
                user.set_password(data.get('password'))
                user.save()

                subscriber = Subscriber.objects.create(
                    user_id=user.id,
                    birthday=data.get('birthday'),
                    library_id=request.user.librarian.library_id,
                    max_device=data.get('max_device'),
                    max_borrow_duration=data.get('max_borrow_duration'),
                    max_download=data.get('max_download'),
                )
                subscriber.save()
                return Response({'success': True, 'data': userSerializer.data}, status=status.HTTP_201_CREATED)
            else:
                return Response({'success': False, 'error': 'The library is full'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'success': False, 'error': 'No permission'}, status=status.HTTP_400_BAD_REQUEST)


class SubscriberDetailView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]
    serializer_class = UserSubscriberSerializer

    def get_queryset(self):
        return User.objects.filter(user_type=UserType.SUBSCRIBER)

    def patch(self, request, *args, **kwargs):

        if request.user.is_admin():
            return Response({'success': False, 'error': 'Admin can not update subscriber'}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.is_librarian():
            data = request.data.dict()
            user = self.get_object()

            serializer = UserSerializer(user, data=data, partial=True)

            serializer.is_valid(raise_exception=True)
            user = serializer.save()
            if data.get('password', '') != '':
                user.set_password(data.get('password'))
                user.save()

            subscriber = Subscriber.objects.filter(user=user).first()
            subscriber.max_download = data.get('max_download')
            subscriber.max_borrow_duration = data.get('max_borrow_duration')
            subscriber.save()

        tokens = Token.objects.filter(user_id=user.id)

        if user.is_active == False:
            tokens.delete()
        return Response({'success': True}, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        instance.is_active = not instance.is_active
        instance.save()

        if instance.is_active == False:
            Token.objects.filter(user_id=instance.id).delete()


class PublisherView(generics.ListAPIView):

    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]
    serializer_class = UserPublisherSerializer
    search_fields = ['username', 'email', 'name', 'short_name', 'phone']
    ordering_fields = ['username', 'email', 'name', 'short_name', 'phone']
    filter_backends = (SearchFilter, OrderingFilter)

    def get_queryset(self):
        return User.objects.filter(user_type=UserType.PUBLISHER).order_by('-id')

    def post(self, request):

        data = request.data.dict()
        username=data.get('username')

        if not checkUsername(username):
            return Response({'success': False, 'message': "Must contain at least 1 uppercase letter, 1 lowercase letter, 1 special character and 1 digit in Username."})
        userSerializer = UserSerializer(data={**data, 'user_type': UserType.PUBLISHER})
        userSerializer.is_valid(raise_exception=True)
        user = userSerializer.save()
        user.set_password(data.get('password'))
        user.save()

        publisher = Publisher.objects.create(user_id=user.id, storage=data.get('storage'))
        publisher.save()
        return Response({'success': True, 'data': userSerializer.data}, status=status.HTTP_201_CREATED)


class PublisherDetailView(generics.RetrieveDestroyAPIView):
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]
    serializer_class = UserPublisherSerializer

    def get_queryset(self):
        return User.objects.filter(user_type=UserType.PUBLISHER)

    def patch(self, request, *args, **kwargs):

        data = request.data.dict()
        user = self.get_object()
        storage = data.get('storage')

        if not request.user.is_admin():
            return Response({'success': False, 'error': 'No permission'}, status=status.HTTP_400_BAD_REQUEST)

        publisher = Publisher.objects.filter(user_id=user.id).first()
        data_media = Media.objects.filter(publisher_id=publisher.user_id).aggregate(size=Sum('file_size'))

        if data_media['size'] is None:
            data_media['size'] = 0.0

        if float(storage) * math.pow(1024, 3) < float(data_media['size']):
            return Response({'error': 'Data update size must be greater than data current size'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UserSerializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        if data.get('password', '') != '':
            user.set_password(data.get('password'))
            user.save()

        publisher.storage = float(storage)
        publisher.save()

        if user.is_active == False:
            Token.objects.filter(user_id=user.id).delete()

        return Response({'success': True}, status=status.HTTP_200_OK)



    def perform_destroy(self, instance):
        instance.is_active = not instance.is_active
        instance.save()

        if instance.is_active == False:
            Token.objects.filter(user_id=instance.id).delete()

class UserDeleteView(generics.RetrieveDestroyAPIView):
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]
    serializer_class = UserPublisherSerializer

    # def get_queryset(self):
    #     user_type=self.request.user.user_type
    #     return User.objects.filter(user_type=user_type)
    def delete(self, request, *args, **kwargs):
        # user_id = kwargs['pk']
        user_state=request.user
        users = request.data.get('users')
        list_users = users.split(',')
        deleted_user_ids=[]
        deleted_library_ids=[]
        for user_id in list_users:
            user=User.objects.filter(id=user_id).first()
            if user is None:
                return Response({'success': False, 'error': 'User does not exist.'})
            if user.user_type==UserType.PUBLISHER:
                if not user_state.is_admin():
                    return Response({'success': False, 'error': 'No permission'}, status=status.HTTP_400_BAD_REQUEST)
                publisher = Publisher.objects.filter(user_id=user.id).first()
                if not publisher:
                    return Response({'success': False, 'message': 'The publisher does not exists.'})

                publisher_contract=LibraryMedia.objects.filter(media__publisher=publisher.user)
                if publisher_contract.count()>0:
                    return Response({'success': False, 'message': 'Cannot delete publisher because their content in contract.'})
                
                deleted_user_ids.append(publisher.user_id)                
            
            elif user.user_type==UserType.LIBRARIAN:
                if not user_state.is_admin():
                    return Response({'success': False, 'error': 'No permission'}, status=status.HTTP_400_BAD_REQUEST)
                librarian = Librarian.objects.filter(user_id=user.id).first()
                if not librarian:
                    return Response({'success': False, 'message': 'The library does not exists.'})

                library_contract=LibraryMedia.objects.filter(library_id=librarian.library_id)
                if library_contract.count()>0:
                    return Response({'success': False, 'message': 'Cannot delete library because their content in contract.'})
                deleted_user_ids.append(librarian.user_id)
                deleted_library_ids.append(librarian.library_id)

            elif user.user_type==UserType.TEACHER:
                if not user_state.is_librarian():
                    return Response({'success': False, 'error': 'No permission'}, status=status.HTTP_400_BAD_REQUEST)
                teacher = Teacher.objects.filter(user_id=user.id).first()            
                if not teacher:
                    return Response({'success': False, 'message': 'The teacher does not exists.'})
                if user_state.librarian.library_id!=teacher.library_id:
                    return Response({'success': False, 'error': 'No permission'})
                deleted_user_ids.append(teacher.user_id)

            elif user.user_type==UserType.SUBSCRIBER:
                if not user_state.is_librarian():
                    return Response({'success': False, 'error': 'No permission'}, status=status.HTTP_400_BAD_REQUEST)
                subscriber = Subscriber.objects.filter(user_id=user.id).first()
                if not subscriber:
                    return Response({'success': False, 'message': 'The subscriber does not exists.'})
                if user_state.librarian.library_id!=subscriber.library_id:
                    return Response({'success': False, 'error': 'No permission'})
                deleted_user_ids.append(subscriber.user_id)
        
        if len(deleted_user_ids)>0:
            User.objects.filter(id__in=deleted_user_ids).delete()
            if len(deleted_library_ids)>0:
                Library.objects.filter(id__in=deleted_library_ids).delete()             
            return Response({'success': True})
        return Response({'success': False})
        

class AdminView(generics.ListAPIView):
    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]
    serializer_class = UserSerializer
    search_fields = ['username', 'email', 'name', 'short_name', 'phone']
    ordering_fields = ['username', 'email', 'name', 'short_name', 'phone']
    filter_backends = (SearchFilter, OrderingFilter)

    def get_queryset(self):
        return User.objects.filter(user_type=UserType.ADMIN).order_by('-id')

    def post(self, request):
        data = request.data.dict()
        userSerializer = UserSerializer(data={**data, 'user_type': UserType.ADMIN})
        userSerializer.is_valid(raise_exception=True)
        user = userSerializer.save()
        user.set_password(data.get('password'))
        user.save()

        admin = Admin.objects.create(user_id=user.id,)
        admin.save()
        return Response({'success': True, 'data': userSerializer.data}, status=status.HTTP_201_CREATED)


class AdminDetailView(generics.RetrieveDestroyAPIView):

    parser_classes = [parsers.MultiPartParser, parsers.JSONParser]
    serializer_class = UserSerializer

    def get_queryset(self):
        return User.objects.filter(user_type=UserType.ADMIN)

    def patch(self, request, *args, **kwargs):
        data = request.data.dict()
        user = self.get_object()

        serializer = UserSerializer(user, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        if data.get('password', '') != '':
            user.set_password(data.get('password'))
            user.save()

        if user.is_active == False:
            Token.objects.filter(user_id=user.id).delete()

        return Response({'success': True}, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        instance.is_active = not instance.is_active
        instance.save()

        if instance.is_active == False:
            Token.objects.filter(user_id=instance.id).delete()


class ImportSubscriberView(views.APIView):
    permission_classes = [IsAuthenticated]

    def random_string(self):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(10))

    def post(self, request, format='json'):
        results = request.data.get('results')

        if not request.user.is_librarian():
            return Response({'success': False, 'error': 'No permission'}, status=status.HTTP_400_BAD_REQUEST)

        number_subscriber = Subscriber.objects.filter(library_id=request.user.librarian.library_id).count()
        number_subscriber_library = Library.objects.filter(id=request.user.librarian.library_id).first().max_subscribers
        if number_subscriber + len(results) >= number_subscriber_library:
            return Response({'success': False, 'error': 'The library does not have enough slots'}, status=status.HTTP_400_BAD_REQUEST)

        list_username = []
        list_email = []

        for user in results:
            index = results.index(user) + 2
            if user['username'] not in list_username:
                if not checkUsername(user['username']):
                    return Response({'success': False, 'message': "Must contain at least 1 uppercase letter, 1 lowercase letter, 1 special character and 1 digit in Username."})
                list_username.append(user['username'])
            else:
                return Response({'success': False, 'error': 'A user with that username already exists.', 'line': str(index)}, status=status.HTTP_400_BAD_REQUEST)

            if user['email'] not in list_username:
                list_username.append(user['email'])
            else:
                return Response({'success': False, 'error': 'A user with that email already exists.', 'line': str(index)}, status=status.HTTP_400_BAD_REQUEST)

            if 'username' not in user or 'email' not in user or 'name' not in user or 'address' not in user or 'phone' not in user or 'short_name' not in user:
                return Response({'success': False, 'error': ['Not enough required fields.']}, status=status.HTTP_400_BAD_REQUEST)

            if not user['phone'].isdigit():
                return Response({'success': False, 'error': ['Phone must be number.']}, status=status.HTTP_400_BAD_REQUEST)

            password = self.random_string()

            userSerializer = UserSerializer(
                data={
                    'username': user['username'],
                    'email': user['email'],
                    'password': password,
                    'address': user['address'],
                    'phone': user['phone'],
                    'short_name': user['short_name'],
                    'user_type': UserType.SUBSCRIBER,
                }
            )
            if userSerializer.is_valid() == False:
                return Response({'success': False, 'error': 'User invalid', 'line': str(index)}, status=status.HTTP_400_BAD_REQUEST)

        library_id = request.user.librarian.library_id
        library = json.dumps(library_id)
        create_subscribers(results, library)

        return Response({'success': True}, status=status.HTTP_200_OK)


class GetAllPublisherView(views.APIView):
    serializer_class = ViewAllPublisherSerializer
    def get(self, request):        
        users = User.objects.filter(is_active=True, user_type=UserType.PUBLISHER)
        data = ViewAllPublisherSerializer(users, many=True).data
        return Response(data)

    def post(self, request):
        name=request.data.get('name')
        if name:
            users = User.objects.filter(is_active=True, user_type=UserType.PUBLISHER,name__icontains=name)
        else:
            users = User.objects.filter(is_active=True, user_type=UserType.PUBLISHER)
        data = ViewAllPublisherSerializer(users, many=True).data
        return Response(data)


class TrackingActionSubscriberView(generics.ListAPIView):
    serializer_class = UsersActivitieSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if self.request.user.is_admin():
            return UsersActivity.objects.filter(user__user_type=UserType.SUBSCRIBER).order_by('-id')
        elif self.request.user.is_librarian():
            return UsersActivity.objects.filter(user__user_type=UserType.SUBSCRIBER, user__subscriber__library_id= self.request.user.librarian.library_id).order_by('-id')


class ShowCurrentSubscriberOfLibraryView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_librarian():
            return Response({'success': False})

        current = Subscriber.objects.filter(library_id=request.user.librarian.library_id).count()
        maxSubscriber = Library.objects.filter(librarians__library_id=request.user.librarian.library_id).first().max_subscribers
        return Response({'library_id': request.user.librarian.library_id, 'current_subscribers': current, 'max_subscribers': maxSubscriber})


class AdminUpdateMaxdeviceView(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UserSubscriberSerializer

    def get_queryset(self):
        return User.objects.filter(user_type=UserType.SUBSCRIBER, is_active=True)

    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        max_device = request.data.get('max_device')

        if not request.user.is_admin():
            return Response({'success': False, 'error': 'No permission'}, status=status.HTTP_400_BAD_REQUEST)

        subscriber = Subscriber.objects.filter(user_id=user.id).first()
        subscriber.max_device = max_device
        subscriber.save()

        list_token = Token.objects.filter(user_id=user.id)
        for token in list_token:
            tracking_action = UsersActivity.objects.create(user_id=user.id, action=UserAction.LOGOUT)
            tracking_action.save()
            token.delete()

        return Response({'success': True})


class ImportTeacherView(views.APIView):
    permission_classes = [IsAuthenticated]

    def random_string(self):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(10))

    def post(self, request, format='json'):

        results = request.data.get('results')

        list_username = []
        list_email = []
        if not request.user.is_librarian():
            return Response({'success': False, 'error': 'No permission'}, status=status.HTTP_400_BAD_REQUEST)

        for user in results:
            index = results.index(user) + 2
            if user['username'] not in list_username:

                if not checkUsername(user['username']):
                    return Response({'success': False, 'message': "Must contain at least 1 uppercase letter, 1 lowercase letter, 1 special character and 1 digit in Username."})
                
                list_username.append(user['username'])
            else:
                return Response({'success': False, 'error': 'A user with that username already exists.', 'line': str(index)}, status=status.HTTP_400_BAD_REQUEST)

            if user['email'] not in list_username:
                list_username.append(user['email'])
            else:
                return Response({'success': False, 'error': 'A user with that email already exists.', 'line': str(index)}, status=status.HTTP_400_BAD_REQUEST)

            if 'username' not in user or 'email' not in user or 'name' not in user or 'address' not in user or 'phone' not in user or 'short_name' not in user:
                return Response({'success': False, 'error': ['Not enough required fields.']}, status=status.HTTP_400_BAD_REQUEST)

            if not user['phone'].isdigit():
                return Response({'success': False, 'error': ['Phone must be number.']}, status=status.HTTP_400_BAD_REQUEST)

            password = self.random_string()

            userSerializer = UserSerializer(
                data={
                    'username': user['username'],
                    'email': user['email'],
                    'password': password,
                    'address': user['address'],
                    'phone': user['phone'],
                    'short_name': user['short_name'],
                    'user_type': UserType.TEACHER,
                }
            )
            if userSerializer.is_valid() == False:
                return Response({'success': False, 'error': 'User invalid', 'line': str(index)}, status=status.HTTP_400_BAD_REQUEST)

        library_id = request.user.librarian.library_id
        library = json.dumps(library_id)
        create_teachers(results, library)

        return Response({'success': True}, status=status.HTTP_200_OK)


class ProfileSubscriberView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.is_subscriber():
            return Response({'success': False, 'error': 'User not subscriber'})

        user = request.user
        library = LibrarySerializer(user.subscriber.library, context={'request': request})
        librarian = Librarian.objects.get(library_id=user.subscriber.library.id)
        userSerializer = UserSerializer(user, context={'request': request}).data
        userLibrarianSerializer = UserSerializer(librarian.user, context={'request': request}).data
        response = {
            'max_download': user.subscriber.max_download,
            'max_borrow_duration': user.subscriber.max_borrow_duration,
            'logo': userSerializer['logo'],
            'library': {'name': librarian.user.name, 'logo': userLibrarianSerializer['logo'], 'short_name': librarian.user.short_name, **library.data,},
        }
        token = request.headers.get('Authorization').split(' ')[-1]
        response = {
            **response,
            'token': token,
            'success': True,
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'name': user.name,
            'short_name': user.short_name,
            'user_type': user.user_type,
        }

        return Response(response)
