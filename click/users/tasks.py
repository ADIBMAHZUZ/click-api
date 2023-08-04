from __future__ import absolute_import, unicode_literals

from celery import shared_task
from click.users.models import User, Subscriber, UserType, Teacher
from click.teacher_notes.serializers import TeacherNotesCreateSerializer
from click.teacher_notes.models import FileType

from django.core.mail import EmailMultiAlternatives, get_connection
from django.contrib.auth.hashers import make_password
from pathlib import Path
from django.conf import settings

import string
import random
import os

@shared_task
def create_subscribers(results, library_id, fail_silently=False):
    mail = []
    data = []
    
    for user in results: 
        
        password = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
        data.append(
            User(username=user['username'], password=make_password(password), 
            email=user['email'], name=user['name'], short_name= user['short_name'], address=user['address'], phone=user['phone'], user_type= UserType.SUBSCRIBER, activate_token= User().generate_key()))
        

        message = f"""<h2>Account successfully created!</h2>
        <p>Your username: {user['username']}</p>
        <p>Your password: {password}</p>
        <p>Please change password when log in.</p>"""
        content = ( "CLICk - Create Account", message, "CLICk <no-reply@click.com>", [user['email']])
        mail.append(content)
    
    create_user = User.objects.bulk_create(data)

    list_sub = []
    for subscriber in create_user:
        list_sub.append(Subscriber(library_id= library_id, user_id= subscriber.id))

    Subscriber.objects.bulk_create(list_sub)

    emails = []
    for subject, content, from_email, recipient in mail:
        html_message = content
        message = EmailMultiAlternatives(subject, content, from_email, recipient)
        message.attach_alternative(html_message, 'text/html')
        emails.append(message)
    get_connection().send_messages(emails)


@shared_task
def create_teachers(results, library_id, fail_silently=False):
    mail = []
    data = []
    
    for user in results: 
        
        password = ''.join(random.choice(string.ascii_lowercase) for i in range(10))
        data.append(
            User(username=user['username'], password=make_password(password), 
            email=user['email'], name=user['name'], short_name= user['short_name'], address=user['address'], phone=user['phone'], user_type= UserType.TEACHER, activate_token= User().generate_key()))
        

        message = f"""<h2>Account successfully created!</h2>
        <p>Your username: {user['username']}</p>
        <p>Your password: {password}</p>
        <p>Please change password when log in.</p>"""
        content = ( "CLICk - Create Account", message, "CLICk <no-reply@click.com>", [user['email']])
        mail.append(content)
    
    create_user = User.objects.bulk_create(data)

    list_sub = []
    for teacher in create_user:
        teacher_notes = TeacherNotesCreateSerializer(data={
            'name': str(teacher.id),
            'file_type': FileType.FOLDER,
            'url': os.path.join(settings.NOTES, str(teacher.id)),
            'teacher': teacher.id 
        })
        teacher_notes.is_valid(raise_exception=True)
        teacher_notes.save()

        Path(os.path.join(settings.MEDIA_ROOT, settings.NOTES, str(teacher.id))).mkdir(parents=True, exist_ok=True)
        list_sub.append(Teacher(library_id= library_id, user_id= teacher.id))

    Teacher.objects.bulk_create(list_sub)

    emails = []
    for subject, content, from_email, recipient in mail:
        html_message = content
        message = EmailMultiAlternatives(subject, content, from_email, recipient)
        message.attach_alternative(html_message, 'text/html')
        emails.append(message)
    get_connection().send_messages(emails)