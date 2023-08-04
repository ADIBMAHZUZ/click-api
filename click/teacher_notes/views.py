from rest_framework import views, status, generics
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from pathlib import Path
from django.conf import settings
from django_filters import rest_framework as filters
from six.moves.urllib.parse import urlparse
from django.db.models.functions import Lower
from django.db.models import Sum
import datetime
import os
import re
import uuid
from os import listdir
from os import path
from shutil import rmtree
from io import StringIO, BytesIO
from itertools import chain
import math
from click.users.models import User, UserType
from click.users.serializers import UserSerializer
from click.teacher_notes.models import TeacherNotesAction, NotesDownloaded, SubscriberAction, TeacherNotes, TeacherNotesDownloaded, TeacherNotesTransaction, SubscriberTransaction, FileType
from click.teacher_notes.serializers import (
    TeacherNotesSerializer,
    TeacherNotesDetailSerializer,
    TeacherSerializer,
    TeacherNotesCreateSerializer,
    TeacherNotesDownloadSerializer,
    TeacherNotesTransactionSerializer,
    TeacherNotesTransactionSerializer,
    TeacherNotesDownloadedSerializer,
)
from click.notification.models import ConfirmUpload, MessageNotification, NotificationProducer, NotificationReceiver, UploadType, NotificationType
from click.notification.serializers import NotificationProducerSerializer, NotificationReceiverSerializer

#limit 3GB for teacher
def limitTeacherStorage():
    return 3 * math.pow(1024, 3)

def fieldSort(e):
    return e['name']


class TeacherNoteDefaultView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, id):
        my_param = request.GET.get('name')

        Path(os.path.join(settings.MEDIA_ROOT, 'teacher_notes')).mkdir(parents=True, exist_ok=True)
        teacher = User.objects.filter(id=id, user_type=UserType.TEACHER, is_active=True).first()
        if teacher is None:
            return Response({'success': False, 'error': 'Teacher notes invalid'})
        teacherSerializer = UserSerializer(teacher, context={'request': request}).data
        api = {'teacher': {'id': teacher.id, 'name': teacher.name, 'preview_url': teacherSerializer["logo"], 'url': teacherSerializer["logo"]}}
        list_data = []

        Path(os.path.join(settings.MEDIA_ROOT, 'teacher_notes', str(id))).mkdir(parents=True, exist_ok=True)
        dirs = os.listdir(os.path.join(settings.MEDIA_ROOT, 'teacher_notes', str(id)))

        for nameFile in os.listdir(os.path.join(settings.MEDIA_ROOT, 'teacher_notes', str(id))):
            name = nameFile
            url = os.path.join(settings.MEDIA_ROOT, 'teacher_notes', str(id), nameFile)
            url_view = os.path.join(request.build_absolute_uri('/')[:-1], settings.TEACHER_NOTES, 'teacher_notes', str(id), nameFile).replace("\\","/")
            get_time = os.path.getctime(url)
            created = datetime.datetime.fromtimestamp(get_time).strftime('%Y-%m-%d')
            type_file = 'folder'
            size = 'null'
            is_borrowed = False
            if os.path.isfile(url):
                type_file = nameFile.split('.')[-1]
                size = round((os.path.getsize(url)) / (1024 * 1024), 2)
                downloaded = NotesDownloaded.objects.filter(subscriber=request.user, url=url_view).first()
                if downloaded is not None:
                    is_borrowed = True
            data = {'name': name, 'url': url_view, 'file_type': type_file, 'size': size, 'created_date': created, 'is_borrowed': is_borrowed}
            list_data.append(data)

        results = []
        if my_param is not None:
            for res in list_data:
                search = re.search(my_param, res['name'])
                if search is not None:
                    results.append(res)
        else:
            results = list_data

        results.sort(reverse=True, key=fieldSort)
        total = len(results)
        num_page = total // 12
        cal = total % 12
        if cal > 0:
            num_page = num_page + 1
        try:
            data_page = int(request.GET['page'])

            if num_page == 0:
                page_next = None
                page_previous = None
                api['notes'] = {'count': total, 'next': page_next, 'previous': page_previous, 'results': results[0:0]}
                api_view = {'results': api}
                return Response(api_view, status=status.HTTP_200_OK)

            if data_page <= num_page and data_page > 0:
                if data_page < num_page and data_page > 1:
                    page_next = request.build_absolute_uri('/')[:-1] + '/api/teacher_notes/' + str(id) + '/?page=' + str(data_page + 1)
                    page_previous = request.build_absolute_uri('/')[:-1] + '/api/teacher_notes/' + str(id) + '/?page=' + str(data_page - 1)
                    len_next = data_page * 12
                    len_pre = len_next - 12

                    api['notes'] = {'count': total, 'next': page_next, 'previous': page_previous, 'results': results[len_pre:len_next]}
                    api_view = {'results': api}
                    return Response(api_view, status=status.HTTP_200_OK)
                if data_page == num_page and num_page > 1:
                    page_next = None
                    page_previous = request.build_absolute_uri('/')[:-1] + '/api/teacher_notes/' + str(id) + '/?page=' + str(data_page - 1)
                    len_next = len(results) // 12 * 12
                    if len(results) % 12 == 0:
                        len_next = len_next - 12
                    api['notes'] = {'count': total, 'next': page_next, 'previous': page_previous, 'results': results[len_next : len(results)]}
                    api_view = {'results': api}
                    return Response(api_view, status=status.HTTP_200_OK)

                if data_page == 1:
                    if num_page == 1:
                        page_next = None
                    else:
                        page_next = request.build_absolute_uri('/')[:-1] + '/api/teacher_notes/' + str(id) + '/?page=' + str(data_page + 1)
                    page_previous = None
                    len_next = len(results) // 12
                    if len_next > 0:
                        len_next = 12
                    else:
                        len_next = len(results)
                    api['notes'] = {'count': total, 'next': page_next, 'previous': page_previous, 'results': results[0:len_next]}
                    api_view = {'results': api}
                    return Response(api_view, status=status.HTTP_200_OK)
        except:
            if num_page <= 1:
                page_next = None
            else:
                page_next = request.build_absolute_uri('/')[:-1] + '/api/teacher_notes/' + str(id) + '/?page=2'

            page_previous = None
            len_next = len(results) // 12
            if len_next > 0:
                len_next = 12
            else:
                len_next = len(results)
            api['notes'] = {'count': total, 'next': page_next, 'previous': page_previous, 'results': results[0:len_next]}
            api_view = {'results': api}
            return Response(api_view, status=status.HTTP_200_OK)

        api['notes'] = {'count': 0, 'next': None, 'previous': None, 'results': results}
        api_view = {'results': api}
        return Response(api_view, status=status.HTTP_200_OK)

    def post(self, request, format='json'):
        folder = request.data.get('folder')
        file_data = request.data.get('file')
        id_user = None
        try:
            temp = folder.split('teacher_notes')
            temp_split = temp[1].split('/')
            id_user = temp_split[1]

            if not request.user.is_teacher():
                return Response({'success': False, 'error': 'No permission'}, status=status.HTTP_400_BAD_REQUEST)

            if not request.user.id == int(id_user):
                return Response({'success': False, 'error': 'No permissions with this directory'}, status=status.HTTP_400_BAD_REQUEST)

            if file_data is None or folder is None:
                return Response({'success': False, 'error': 'Data may not be blank'}, status=status.HTTP_400_BAD_REQUEST)

            if not os.path.exists(os.path.join(settings.MEDIA_ROOT, folder.split('public/')[1])):
                return Response({'success': False, 'error': 'Folder does not exist'}, status=status.HTTP_400_BAD_REQUEST)

            path = os.path.join(settings.MEDIA_ROOT, folder.split('public/')[1], str(file_data))
            if os.path.exists(path):
                return Response({'success': False, 'error': 'File already exist'}, status=status.HTTP_400_BAD_REQUEST)

            create = open(path, 'wb').write(file_data.file.read())
            return Response({'success': True}, status=status.HTTP_201_CREATED)

        except:
            return Response({'success': False, 'error': 'No permissions with this directory'}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, id):
        pathsrc = request.data.get('path')
        try:
            if not request.user.is_teacher():
                return Response({'success': False, 'error': 'No permission'}, status=status.HTTP_400_BAD_REQUEST)

            path = os.path.join(settings.MEDIA_ROOT, pathsrc.split('public/')[1])

            if not os.path.exists(path):
                return Response({'success': False, 'error': 'Folder or file does not exists'}, status=status.HTTP_400_BAD_REQUEST)

            temp = path.split('teacher_notes')
            temp_split = temp[1].split('/')
            id_user = temp_split[1]

            if not request.user.id == int(id_user):
                return Response({'success': False, 'error': 'No permissions with this directory'}, status=status.HTTP_400_BAD_REQUEST)

            if os.path.isdir(path):
                list_src = []
                for dirname, dirnames, filenames in os.walk(path):
                    for filename in filenames:
                        format_path = os.path.join(dirname, filename)
                        format_src = format_path.split('public/')
                        src = os.path.join(request.build_absolute_uri('/')[:-1], 'public', format_src[1])
                        list_src.append(src)
                TeacherNotesAction.objects.filter(url__in=list_src).delete()
                NotesDownloaded.objects.filter(url__in=list_src).delete()
                rmtree(path)
                return Response({'success': True}, status=status.HTTP_200_OK)
            TeacherNotesAction.objects.filter(url=pathsrc).delete()
            NotesDownloaded.objects.filter(url=pathsrc).delete()
            os.remove(path)
            return Response({'success': True}, status=status.HTTP_200_OK)

        except:
            return Response({'success': False, 'error': 'No permissions with this directory'}, status=status.HTTP_400_BAD_REQUEST)


class CreateFolder(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # public/teacher_notes/3
        dirname = request.data.get('dirname')
        folder_name = request.data.get('folder')
        
        try:
            temp = dirname.split('teacher_notes')
            temp_split = temp[1].split('/')
            id = temp_split[1]
            if not request.user.is_teacher():
                return Response({'success': False, 'error': 'No permission'}, status=status.HTTP_400_BAD_REQUEST)

            if not request.user.id == int(id):                
                return Response({'success': False, 'error': 'No permissions with this directory'}, status=status.HTTP_400_BAD_REQUEST)

            if folder_name == 'public':
                return Response({'success': False, 'error': 'Can not create folder name "public". Please choose other name.'}, status=status.HTTP_400_BAD_REQUEST)

            if dirname is None or folder_name is None:
                return Response({'success': False, 'error': 'Path does not exist'}, status=status.HTTP_400_BAD_REQUEST)

            folder=os.path.isdir(os.path.join(settings.MEDIA_ROOT, dirname.split('public/')[1], folder_name))
            if folder:
                return Response({'success': False, 'error': 'Folder already exists'}, status=status.HTTP_400_BAD_REQUEST)

            path = os.path.join(settings.MEDIA_ROOT, dirname.split('public/')[1], folder_name)
            os.mkdir(path)
            return Response({'success': True}, status=status.HTTP_201_CREATED)

        except:
            return Response({'success': False, 'error': 'No permissions with this directory'}, status=status.HTTP_400_BAD_REQUEST)


class TeacherNoteListView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id, format='json'):

        my_param = request.GET.get('name')

        folder = str(request.data.get('folder'))
        Path(os.path.join(settings.MEDIA_ROOT, 'teacher_notes')).mkdir(parents=True, exist_ok=True)
        teacher = User.objects.filter(id=id, is_active=True).first()
        if teacher is None:
            return Response({'success': False, 'error': 'teacher notes invalid'})

        teacherSerializer = UserSerializer(teacher, context={'request': request}).data
        api = {'teacher': {'id': teacher.id, 'name': teacher.name, 'preview_url': teacherSerializer["logo"], 'url': teacherSerializer["logo"]}}
        result_data = []
        if path.exists(os.path.join(settings.MEDIA_ROOT, folder.split('public/')[1])):

            if os.path.isfile(os.path.join(settings.MEDIA_ROOT, folder.split('public/')[1])):
                get_name = folder.split('/')
                name = get_name[len(get_name) - 1]
                url = os.path.join(settings.MEDIA_ROOT, folder.split('public/')[1])
                url_view = folder
                get_time = os.path.getctime(url)
                created = datetime.datetime.fromtimestamp(get_time).strftime('%Y-%m-%d')
                get_type = name.split('.')
                type_file = get_type[-1]
                size = round((os.path.getsize(url)) / (1024 * 1024), 2)
                downloaded = NotesDownloaded.objects.filter(subscriber=request.user, url=url_view).first()
                is_borrowed = False
                if downloaded is not None:
                    is_borrowed = True
                data = {'name': name, 'url': url_view, 'file_type': type_file, 'size': size, 'created_date': created, 'is_borrowed': is_borrowed}
                result_data.append(data)
            else:
                dirs = os.listdir(os.path.join(settings.MEDIA_ROOT, folder.split('public/')[1]))
                for nameFile in dirs:
                    name = nameFile
                    url = os.path.join(settings.MEDIA_ROOT, folder.split('public/')[1], nameFile)
                    url_view = os.path.join(request.build_absolute_uri('/')[:-1], settings.TEACHER_NOTES, folder.split('public/')[1], nameFile)
                    get_time = os.path.getctime(url)
                    created = datetime.datetime.fromtimestamp(get_time).strftime('%Y-%m-%d')
                    type_file = 'folder'
                    size = None
                    is_borrowed = False
                    if os.path.isfile(url):
                        type_file = nameFile.split('.')[-1]
                        size = round((os.path.getsize(url)) / (1024 * 1024), 2)
                        downloaded = NotesDownloaded.objects.filter(subscriber=request.user, url=url_view).first()
                        if downloaded is not None:
                            is_borrowed = True
                    data = {'name': name, 'url': url_view, 'file_type': type_file, 'size': size, 'created_date': created, 'is_borrowed': is_borrowed}
                    result_data.append(data)
            result = []
            if my_param is not None:
                for res in result_data:
                    search = re.search(my_param, res['name'])
                    if search is not None:
                        result.append(res)
            else:
                result = result_data

            result.sort(reverse=True, key=fieldSort)
            total = len(result)
            num_page = total // 12
            cal = total % 12
            if cal > 0:
                num_page = num_page + 1
            try:
                data_page = int(request.GET['page'])
                if num_page == 0:
                    page_next = None
                    page_previous = None
                    api['notes'] = {'count': total, 'next': page_next, 'previous': page_previous, 'results': result[0:0]}
                    api_view = {'results': api}
                    return Response(api_view, status=status.HTTP_200_OK)

                if data_page <= num_page and data_page > 0:
                    if data_page < num_page and data_page > 1:
                        page_next = request.build_absolute_uri('/')[:-1] + '/api/teacher_notes/' + str(id) + '/list' + '/?page=' + str(data_page + 1)
                        page_previous = request.build_absolute_uri('/')[:-1] + '/api/teacher_notes/' + str(id) + '/list' + '/?page=' + str(data_page - 1)
                        len_next = data_page * 12
                        len_pre = len_next - 12

                        api['notes'] = {'count': total, 'next': page_next, 'previous': page_previous, 'results': result[len_pre:len_next]}
                        api_view = {'results': api}
                        return Response(api_view, status=status.HTTP_200_OK)
                    if data_page == num_page and num_page > 1:
                        page_next = None
                        page_previous = request.build_absolute_uri('/')[:-1] + '/api/teacher_notes/' + str(id) + '/list' + '/?page=' + str(data_page - 1)
                        len_next = len(result) // 12 * 12
                        if len(result) % 12 == 0:
                            len_next = len_next - 12
                        api['notes'] = {'count': total, 'next': page_next, 'previous': page_previous, 'results': result[len_next : len(result)]}
                        api_view = {'results': api}
                        return Response(api_view, status=status.HTTP_200_OK)

                    if data_page == 1:
                        if num_page == 1:
                            page_next = None
                        else:
                            page_next = request.build_absolute_uri('/')[:-1] + '/api/teacher_notes/' + str(id) + '/list' + '/?page=' + str(data_page + 1)
                        page_previous = None
                        len_next = len(result) // 12
                        if len_next > 0:
                            len_next = 12
                        else:
                            len_next = len(result)
                        api['notes'] = {'count': total, 'next': page_next, 'previous': page_previous, 'results': result[0:len_next]}
                        api_view = {'results': api}
                        return Response(api_view, status=status.HTTP_200_OK)
            except:
                if num_page <= 1:
                    page_next = None
                else:
                    page_next = request.build_absolute_uri('/')[:-1] + '/api/teacher_notes/' + str(id) + '/list' + '/?page=2'

                page_previous = None
                len_next = len(result) // 12
                if len_next > 0:
                    len_next = 12
                else:
                    len_next = len(result)
                api['notes'] = {'count': total, 'next': page_next, 'previous': page_previous, 'results': result[0:len_next]}
                api_view = {'results': api}
                return Response(api_view, status=status.HTTP_200_OK)

        else:
            api['notes'] = {'count': 0, 'next': None, 'previous': None, 'results': result}
            api_view = {'results': api}
            return Response(api_view, status=status.HTTP_200_OK)


class TeacherNotesDownload(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        try:
            url = request.data.get('url')
            if not request.user.is_subscriber():
                return Response({'success': False, 'error': 'No permissions'}, status=status.HTTP_200_OK)
            url_path = (url.split('public'))[-1]
            path = settings.MEDIA_ROOT + url_path
            if not os.path.isfile(path):
                return Response({'success': False, 'error': 'Path must be file'}, status=status.HTTP_200_OK)

            temp = path.split('teacher_notes/')
            teacher_path = temp[1]
            teacher_id = (teacher_path.split('/'))[0]

            log = NotesDownloaded.objects.filter(url=url, subscriber_id=request.user.id).first()
            if log is not None:
                return Response({'success': False, 'error': 'you have downloaded this note'})

            teacher_download = NotesDownloaded.objects.create(
                name=path.split('/')[-1],
                size=os.path.getsize(path),
                file_type=path.split('.')[-1],
                url=url,
                created_date=datetime.datetime.fromtimestamp(os.path.getctime(path)).strftime('%Y-%m-%d'),
                subscriber_id=request.user.id,
                teacher_id=teacher_id,
            )
            teacher_download.save()

            action = TeacherNotesAction.objects.create(name=path.split('/')[-1], url=url, action=SubscriberAction.DOWNLOADED, subscriber_id=request.user.id)
            action.save()
            return Response({'success': True}, status=status.HTTP_200_OK)

        except:
            return Response({'success': False, 'error': 'Folder invalid'}, status=status.HTTP_200_OK)


class TeacherNotesReturn(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, id):
        url = request.data.get('url')
        if request.user.is_subscriber():
            log = NotesDownloaded.objects.filter(url=url, subscriber_id=request.user.id).first()
            if log is None:
                return Response({'success': False, 'error': 'you have not downloaded this note'})

            url_path = (url.split('public'))[-1]
            path = settings.MEDIA_ROOT + url_path
            action = TeacherNotesAction(name=path.split('/')[-1], url=url, action=SubscriberAction.RETURN, subscriber_id=request.user.id)
            action.save()
            log.delete()
            return Response({'success': True}, status=status.HTTP_200_OK)
        return Response({'success': False, 'error': 'No permissions'}, status=status.HTTP_200_OK)


class TeacherNotesDownloadedViews(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TeacherNotesSerializer

    def get(self, request):
        serializer = None
        if request.user.is_subscriber():
            query_set = NotesDownloaded.objects.filter(subscriber_id=request.user.id)
            serializer = TeacherNotesSerializer(query_set, many=True, context={'request': request}).data
            data = {'results': serializer}
            return Response({'results': serializer}, status=status.HTTP_200_OK)
        return Response({'success': False, 'error': 'no permission'}, status=status.HTTP_200_OK)


# new


class PagingTeacherNotes(PageNumberPagination):
    page_size = 20


class TeacherNoteView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TeacherNotesDetailSerializer
    pagination_class = PagingTeacherNotes

    def post(self, request, pk):
        if request.user.is_teacher():
            user = User.objects.filter(id=pk, is_active=True).first()

        if request.user.is_subscriber():
            user = User.objects.filter(is_active=True, teacher__library_id=request.user.subscriber.library_id, id=pk).first()

        if user is None:
            return Response({'success': False, 'error': 'Note invalid'})

        if request.user.is_teacher() and request.user.id != pk:
            return Response({'success': False, 'error': 'No permission'})

        if TeacherNotes.objects.filter(url=os.path.join(settings.NOTES, str(pk)), teacher_id=pk).first() is None:
            serializer = TeacherNotesCreateSerializer(data={'name': str(pk), 'file_type': FileType.FOLDER, 'url': os.path.join(settings.NOTES, str(pk)), 'teacher': pk,})
            serializer.is_valid(raise_exception=True)
            serializer.save()

        queryset = TeacherNotes.objects.filter(teacher_id=pk)

        name = request.query_params.get('q')
        folder = request.data.get('folder')
        teacher = TeacherSerializer(user, context={'request': request}).data
        if name is not None and name != '':
            queryset = queryset.filter(name__icontains=name)
        if folder is not None and folder != '':
            url = os.path.relpath(folder, os.path.join(request.build_absolute_uri('/')[:-1], settings.TEACHER_NOTES))
            parent = TeacherNotes.objects.filter(url=url, teacher_id=pk).first()
            if parent is None:
                return Response({'success': False, 'error': 'Folder does not exists'})

            queryset = queryset.filter(parent_folder=parent.id)
        elif folder is None or folder == '':
            url = os.path.join(settings.NOTES, str(pk))
            parent = TeacherNotes.objects.filter(url=url, teacher_id=pk).first()
            queryset = queryset.filter(parent_folder=parent.id)

        transfer_folder = queryset.filter(file_type=FileType.FOLDER).order_by(Lower('name'))
        transfer_file = queryset.exclude(file_type=FileType.FOLDER).order_by(Lower('name'))
        queryset = list(chain(transfer_folder, transfer_file))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            result = self.get_paginated_response(serializer.data)
            data = result.data
        else:
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data

        payload = {'results': {'teacher': teacher, 'notes': data,}}
        return Response(payload)


class TeacherNotesUploadViews(generics.ListCreateAPIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        data = request.data.dict()
        name = data.get('name')
        folder = data.get('folder')
        file_type = data.get('type')
        check = False

       

        url = os.path.relpath(folder, os.path.join(request.build_absolute_uri('/')[:-1], settings.TEACHER_NOTES))

        notes = TeacherNotes.objects.filter(url=url, teacher=request.user).first()
        if not request.user.is_teacher():
            return Response({'success': False, 'error': 'No permission'})

        if notes is None:
            return Response({'success': False, 'error': 'Folder does not exists'})

        if not (file_type == FileType.FOLDER or file_type == FileType.FILE):
            return Response({'success': False, 'error': 'Data invalid'})

        Path(os.path.join(settings.MEDIA_ROOT, settings.NOTES, str(request.user.id))).mkdir(parents=True, exist_ok=True)
        if file_type == FileType.FOLDER:
            name_notes = TeacherNotes.objects.filter(name=name, parent_folder=notes.id, file_type=FileType.FOLDER, teacher=request.user).first()
            if name_notes is not None:
                return Response({'success': False, 'error': 'Folder already exists'})
            
            if not isinstance(name, str):
                return Response({'success': False, 'error': 'File type invalid'})

            url = os.path.join(notes.url, name)
            serializer = TeacherNotesCreateSerializer(data={**data, 'file_type': FileType.FOLDER, 'url': url, 'teacher': request.user.id, 'parent_folder': notes.id})
            serializer.is_valid(raise_exception=True)
            serializer.save()

            path = os.path.join(settings.MEDIA_ROOT, notes.url, name)
            Path(path).mkdir(parents=True, exist_ok=True)

        if file_type == FileType.FILE:

            



            if isinstance(name, str):
                return Response({'success': False, 'error': 'File type invalid'})

            name_notes = TeacherNotes.objects.filter(name=str(name), parent_folder=notes.id, teacher=request.user).exclude(file_type=FileType.FOLDER).first()
            if name_notes is not None:
                return Response({'success': False, 'error': 'File already exists'})

            path = os.path.join(settings.MEDIA_ROOT, notes.url, str(name))
            url = os.path.join(notes.url, str(name))


            # check size of file

            file_size = os.path.getsize(name.temporary_file_path())


            current_data = TeacherNotes.objects.filter(teacher_id=request.user.id).aggregate(size=Sum('size'))
            if current_data['size'] is None:
                current_data['size'] = 0

            if file_size / (1024 * 1024) >= 700:
                return Response({'success': False, 'error': 'Your file size should be less than 700MB!', 'code': 'CLC403'})

            data_size = float(file_size) + float(current_data['size'])
            if data_size > math.pow(1024, 3)*request.user.teacher.storage:
                return Response({'success': False, 'error': 'Not enough storage', 'code': 'CLC404'})

            # check size of file


            serializer = TeacherNotesCreateSerializer(
                data={'name': str(name), 'file_type': str(name).split('.')[-1], 'url': url, 'size': os.path.getsize(name.temporary_file_path()), 'teacher': request.user.id, 'parent_folder': notes.id}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            open(path, 'wb').write(name.file.read())

        # notification
        producer = NotificationProducerSerializer(data={'user': request.user.id})
        producer.is_valid(raise_exception=True)
        noti_producer = producer.save()

        receiver = NotificationReceiverSerializer(
            data={
                'producer': noti_producer.id,
                'notification_type': NotificationType.CONFIRM_UPLOAD,
                'message': MessageNotification.LOG_UPLOAD_TEACHER_NOTES,
                'user': User.objects.filter(user_type=UserType.ADMIN).first().id,
            }
        )
        receiver.is_valid(raise_exception=True)
        noti_receiver = receiver.save()

        if file_type != FileType.FOLDER:
            name = str(name)

        confirm = ConfirmUpload.objects.create(receiver=noti_receiver, upload_type=UploadType.SCHOOL_HISTORY, name=name)
        confirm.save()
        return Response({'success': True})


class SubscriberDownloadNotesView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TeacherNotesDetailSerializer

    def get_queryset(self):
        return TeacherNotes.objects.filter(teacher__is_active=True, teacher__teacher__library_id=self.request.user.subscriber.library_id).exclude(file_type=FileType.FOLDER)

    def post(self, request, pk):
        note = self.get_object()

        log = TeacherNotesDownloaded.objects.filter(note=note, subscriber_id=request.user.id).first()
        if log is not None:
            return Response({'success': False, 'error': 'You have downloaded this note'})

        transaction = TeacherNotesTransactionSerializer(data={'note': note.id, 'subscriber': request.user.id, 'action': SubscriberTransaction.DOWNLOADED})
        transaction.is_valid(raise_exception=True)
        transaction.save()

        download = TeacherNotesDownloadSerializer(data={'note': note.id, 'subscriber': request.user.id})
        download.is_valid(raise_exception=True)
        download.save()

        return Response({'success': True})


class SubscriberReturnNotesView(generics.RetrieveAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TeacherNotesDetailSerializer

    def get_queryset(self):
        return TeacherNotes.objects.filter(teacher__is_active=True, teacher__teacher__library_id=self.request.user.subscriber.library_id)

    def post(self, request, pk):
        note = self.get_object()

        log = TeacherNotesDownloaded.objects.filter(note=note, subscriber_id=request.user.id).first()
        if log is None:
            return Response({'success': False, 'error': 'You have not downloaded this note'})

        transaction = TeacherNotesTransactionSerializer(data={'note': note.id, 'subscriber': request.user.id, 'action': SubscriberTransaction.RETURNED})
        transaction.is_valid(raise_exception=True)
        transaction.save()

        TeacherNotesDownloaded.objects.filter(note=note, subscriber_id=request.user.id).delete()

        return Response({'success': True})


class TeacherNotesDeleteView(generics.RetrieveDestroyAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = TeacherNotesDetailSerializer

    def get_queryset(self):
        return TeacherNotes.objects.filter(teacher=self.request.user, teacher__is_active=True, teacher__teacher__library_id=self.request.user.teacher.library_id)

    def perform_destroy(self, instance):
        path = os.path.join(settings.MEDIA_ROOT, instance.url)
        if instance.file_type == FileType.FOLDER:
            TeacherNotes.objects.filter(url__startswith=instance.url, teacher_id=instance.teacher_id).delete()
            TeacherNotesDownloaded.objects.filter(note__url__startswith=instance.url, note__teacher_id=instance.teacher_id).delete()
            TeacherNotesTransaction.objects.filter(note__url__startswith=instance.url, note__teacher_id=instance.teacher_id).delete()
            instance.delete()
            rmtree(path)
        else:
            TeacherNotesDownloaded.objects.filter(note=instance.id, note__teacher_id=instance.teacher_id).delete()
            TeacherNotesTransaction.objects.filter(note=instance.id, note__teacher_id=instance.teacher_id).delete()
            instance.delete()
            os.remove(path)

class TeacherNotesMultiDeleteView(views.APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs):
        if request.user.is_teacher():
            ids = request.get('ids').split(',')
            queryset = TeacherNotes.objects.filter(id__in=ids)
            serializer = TeacherNotesSerializer(queryset, many=True)
            return Response({'success': True,'results': serializer.data})
        return Response({'success': False, 'error': 'No permission'})
        

    def delete(self, request, *args, **kwargs):
        if not request.user.is_teacher():
            return Response({'success': False, 'error': 'No permission'})
        list_id=request.data.get('ids')
        ids = list_id.split(',')
        if ids:
            queryset = TeacherNotes.objects.filter(id__in=ids)
            for note in queryset:
                
                if note.teacher.id==request.user.id:
                    path = os.path.join(settings.MEDIA_ROOT, note.url)
                    if note.file_type == FileType.FOLDER:
                        TeacherNotes.objects.filter(url__startswith=note.url, teacher_id=note.teacher_id).delete()
                        TeacherNotesDownloaded.objects.filter(note__url__startswith=note.url, note__teacher_id=note.teacher_id).delete()
                        TeacherNotesTransaction.objects.filter(note__url__startswith=note.url, note__teacher_id=note.teacher_id).delete()
                        note.delete()
                        rmtree(path)
                    else:
                        TeacherNotesDownloaded.objects.filter(note=note.id, note__teacher_id=note.teacher_id).delete()
                        TeacherNotesTransaction.objects.filter(note=note.id, note__teacher_id=note.teacher_id).delete()
                        note.delete()
                        os.remove(path)
                else:
                    return Response({'success': False, 'error': 'No permission'})            
        return Response({'success': True})  

class TeacherNotesTransactionViews(views.APIView):
    serializer_class = TeacherNotesDownloadedSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_subscriber():
            notes = TeacherNotes.objects.filter(notes_downloaded__subscriber_id=request.user.id)
            data = TeacherNotesDownloadedSerializer(notes, many=True, context={'request': request}).data
            return Response({'results': data})
        return Response({'success': False, 'error': 'No permission'})


class TeacherNotesRenameViews(generics.RetrieveUpdateAPIView):
    serializer_class = TeacherNotesDetailSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return TeacherNotes.objects.filter(teacher=self.request.user, teacher__is_active=True).exclude(parent_folder=0)

    def patch(self, request, *args, **kwargs):
        note = self.get_object()
        new_name = request.data.get('name')
        regex = re.compile('[@"!#$%^&*()<>?/\|}{~;]')
        regex2 = re.compile("'")

        if regex.search(new_name) != None or regex2.search(new_name) != None:
            return Response({'success': False, 'error': 'Name cannot contain special characters'})

        if new_name == '' or new_name is None:
            return Response({'success': False, 'error': 'Name invalid'})

        if note.file_type != FileType.FOLDER:
            new_name = new_name + "." + note.name.split('.')[-1]
        parent = TeacherNotes.objects.filter(parent_folder=note.parent_folder, teacher_id=note.teacher_id, name__iexact=new_name).exclude(id=note.id).first()
        if parent is not None:
            return Response({'success': False, 'error': 'Name already exists'})

        if note.file_type == FileType.FOLDER:
            parent = TeacherNotes.objects.filter(id=note.parent_folder).first()
            new_url = os.path.join(parent.url, new_name)

            note_sub = TeacherNotes.objects.filter(url__startswith=note.url).exclude(id=note.id)
            for sub in note_sub:
                split_url = os.path.relpath(sub.url, note.url)
                re_url = os.path.join(new_url, split_url)
                sub.url = re_url
                sub.save()

            src = os.path.join(settings.MEDIA_ROOT, note.url)
            des = os.path.join(settings.MEDIA_ROOT, parent.url, new_name)
            os.rename(src, des)

            note.name = new_name
            note.url = new_url
            note.save()

        else:
            parent = TeacherNotes.objects.filter(id=note.parent_folder).first()
            new_url = os.path.join(parent.url, new_name)

            src = os.path.join(settings.MEDIA_ROOT, note.url)
            des = os.path.join(settings.MEDIA_ROOT, parent.url, new_name)
            os.rename(src, des)

            note.name = new_name
            note.url = new_url
            note.save()

        return Response({'success': True})

