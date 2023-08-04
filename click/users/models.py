import binascii
import os
import random
import string
import uuid

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail

from model_utils.models import TimeStampedModel

from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator

from django.db import models


class AbstractUser(AbstractBaseUser, PermissionsMixin):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions.

    Username and password are required. Other fields are optional.
    """
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    email = models.EmailField(_('email address'), blank=True)
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
    )
    is_active = models.BooleanField(
        _('active'),
        default=True,
    )

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def email_user(self, subject, message, from_email=None, **kwargs):
        """Send an email to this user."""
        send_mail(subject, message, from_email, [self.email], **kwargs)

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        abstract = True


class UserType(models.TextChoices):
    ADMIN = 'admin', _('Admin')
    SUBSCRIBER = 'subscriber', _('Subscriber')
    TEACHER = 'teacher', _('Teacher')
    LIBRARIAN = 'librarian', _('Librarian')
    PUBLISHER = 'publisher', _('Publisher')


def user_logo_directory_path(instance, filename):
    return os.path.join('user_logo', "{}.{}".format(uuid.uuid4(), filename.split('.')[-1]))


class User(AbstractUser, TimeStampedModel):
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=50, choices=UserType.choices)
    activate_token = models.CharField(max_length=40, null=True, blank=True)
    activate_time = models.DateTimeField(null=True, blank=True)
    name = models.CharField(max_length=50, null=True, blank=True)
    short_name = models.CharField(max_length=50, null=True, blank=True)
    address = models.CharField(max_length=500, null=True, blank=True)
    phone = models.CharField(max_length=20, null=True, blank=True)
    logo = models.ImageField(upload_to=user_logo_directory_path, null=True)

    def get_profile(self):
        if self.is_admin():
            profile = {}
        elif self.is_subscriber():
            profile = Subscriber.objects.get(user_id=self.id)
        elif self.is_librarian():
            profile = Librarian.object.get(user_id=self.id)
        elif self.is_publisher():
            profile = Publisher.object.get(user_id=self.id)
        elif self.is_teacher():
            profile = Teacher.object.get(user_id=self.id)

        return profile

    def is_admin(self):
        if self.user_type == UserType.ADMIN:
            return True

        return False

    def is_subscriber(self):
        if self.user_type == UserType.SUBSCRIBER:
            return True

        return False

    def is_librarian(self):
        if self.user_type == UserType.LIBRARIAN:
            return True

        return False

    def is_publisher(self):
        if self.user_type == UserType.PUBLISHER:
            return True

        return False

    def is_teacher(self):
        if self.user_type == UserType.TEACHER:
            return True

        return False

    def save(self, *args, **kwargs):
        if not self.id:
            self.activate_token = self.generate_key()

        return super().save(*args, **kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    class Meta:
        db_table = 'users_user'


class Token(models.Model):
    """
    The default authorization token model.
    """
    key = models.CharField(_("Key"), max_length=40, primary_key=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='auth_tokens', on_delete=models.CASCADE)
    created = models.DateTimeField(_("Created"), auto_now_add=True)
    device = models.CharField(max_length=100, null=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super().save(*args, **kwargs)

    def generate_key(self):
        return binascii.hexlify(os.urandom(20)).decode()

    def __str__(self):
        return self.key

    class Meta:
        db_table = 'users_token'


class ForgotPasswordToken(models.Model):
    """
    The default authorization token model.
    """
    key = models.CharField(_("Key"), max_length=40, primary_key=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, related_name='auth_forgot_password_token',
        on_delete=models.CASCADE, verbose_name=_("User")
    )
    created = models.DateTimeField(_("Created"), auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super().save(*args, **kwargs)

    def generate_key(self):
        # return binascii.hexlify(os.urandom(20)).decode()

        return ''.join(random.choice(string.ascii_uppercase) for i in range(6))

    def __str__(self):
        return self.key

    class Meta:
        db_table = 'users_forgot_password_token'


class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin')


class Publisher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='publisher')
    storage = models.FloatField(default=1.0)

def get_id(self, request):
    user = request.user.librarian.library_id
    return user

def entire_background_image_directory_path(instance, filename):
    return os.path.join('library', str(instance.id),"{}.{}".format('entire_background_image', filename.split('.')[-1]))

def media_background_image_directory_path(instance, filename):
    return os.path.join('library', str(instance.id),"{}.{}".format('media_background_image', filename.split('.')[-1]))

def school_news_board_background_image_directory_path(instance, filename):
    return os.path.join('library', str(instance.id),"{}.{}".format('school_news_board_background_image', filename.split('.')[-1]))

def teacher_notes_background_image_directory_path(instance, filename):
    return os.path.join('library', str(instance.id), "{}.{}".format('teacher_notes_background_image', filename.split('.')[-1]))

def learning_material_background_image_directory_path(instance, filename):
    return os.path.join('library', str(instance.id), "{}.{}".format('learning_material_background_image', filename.split('.')[-1]))

def the_school_history_background_image_directory_path(instance, filename):
    return os.path.join('library', str(instance.id), "{}.{}".format('the_school_history_background_image', filename.split('.')[-1]))

def student_content_background_image_directory_path(instance, filename):
    return os.path.join('library', str(instance.id), "{}.{}".format('student_content_background_image', filename.split('.')[-1]))

class Library(TimeStampedModel, models.Model):

    is_active = models.BooleanField(default=True)
    max_subscribers = models.IntegerField(default=100)

    # theme
    entire_background_type = models.CharField(max_length=100, null=True)
    entire_background_image = models.ImageField(upload_to= entire_background_image_directory_path, null=True)
    entire_background_color = models.CharField(max_length=100, null=True)

    media_title_en = models.CharField(max_length=100, null=True, default="Library Books, Videos & Musics")
    media_title_ms = models.CharField(max_length=100, null=True, default="Buku Perpustakaan, Video & Muzik")
    media_title_color = models.CharField(max_length=100, null=True)
    media_border_color = models.CharField(max_length=100, null=True)
    media_badge_color = models.CharField(max_length=100, null=True)
    media_icon_color = models.CharField(max_length=100, null=True)
    media_background_transparent = models.CharField(max_length=100, null=True)
    media_background_type = models.CharField(max_length=100, null=True)
    media_background_color = models.CharField(max_length=100, null=True)
    media_background_image = models.ImageField(upload_to= media_background_image_directory_path, null=True)

    school_news_board_title_en = models.CharField(max_length=100, null=True, default="School News Board")
    school_news_board_title_ms = models.CharField(max_length=100, null=True, default="Lembaga Berita Sekolah")
    school_news_board_title_color = models.CharField(max_length=100, null=True)
    school_news_board_border_color = models.CharField(max_length=100, null=True)
    school_news_board_badge_color = models.CharField(max_length=100, null=True)
    school_news_board_icon_color = models.CharField(max_length=100, null=True)
    school_news_board_background_transparent = models.CharField(max_length=100, null=True)
    school_news_board_background_type = models.CharField(max_length=100, null=True)
    school_news_board_background_color = models.CharField(max_length=100, null=True)
    school_news_board_background_image = models.ImageField(upload_to= school_news_board_background_image_directory_path, null=True)

    teacher_notes_title_en = models.CharField(max_length=100, null=True, default="Teacher Notes")
    teacher_notes_title_ms = models.CharField(max_length=100, null=True, default="Nota Guru")
    teacher_notes_title_color = models.CharField(max_length=100, null=True)
    teacher_notes_border_color = models.CharField(max_length=100, null=True)
    teacher_notes_badge_color = models.CharField(max_length=100, null=True)
    teacher_notes_icon_color = models.CharField(max_length=100, null=True)
    teacher_notes_background_transparent = models.CharField(max_length=100, null=True)
    teacher_notes_background_type = models.CharField(max_length=100, null=True)
    teacher_notes_background_color = models.CharField(max_length=100, null=True)
    teacher_notes_background_image = models.ImageField(upload_to= teacher_notes_background_image_directory_path, null=True)

    learning_material_title_en = models.CharField(max_length=100, null=True, default="Learning Materials")
    learning_material_title_ms = models.CharField(max_length=100, null=True, default="Bahan Pembelajaran")
    learning_material_title_color = models.CharField(max_length=100, null=True)
    learning_material_border_color = models.CharField(max_length=100, null=True)
    learning_material_badge_color = models.CharField(max_length=100, null=True)
    learning_material_icon_color = models.CharField(max_length=100, null=True)
    learning_material_background_transparent = models.CharField(max_length=100, null=True)
    learning_material_background_type = models.CharField(max_length=100, null=True)
    learning_material_background_color = models.CharField(max_length=100, null=True)
    learning_material_background_image = models.ImageField(upload_to= learning_material_background_image_directory_path, null=True)

    the_school_history_title_en = models.CharField(max_length=100, null=True, default="The School History")
    the_school_history_title_ms = models.CharField(max_length=100, null=True, default="Sejarah Sekolah")
    the_school_history_title_color = models.CharField(max_length=100, null=True)
    the_school_history_border_color = models.CharField(max_length=100, null=True)
    the_school_history_icon_color = models.CharField(max_length=100, null=True)
    the_school_history_badge_color = models.CharField(max_length=100, null=True)
    the_school_history_background_transparent = models.CharField(max_length=100, null=True)
    the_school_history_background_type = models.CharField(max_length=100, null=True)
    the_school_history_background_color = models.CharField(max_length=100, null=True)
    the_school_history_background_image = models.ImageField(upload_to= the_school_history_background_image_directory_path, null=True)

    student_content_title_en = models.CharField(max_length=100, null=True, default="Student Content")
    student_content_title_ms = models.CharField(max_length=100, null=True, default="Sejarah Sekolah")
    student_content_title_color = models.CharField(max_length=100, null=True)
    student_content_border_color = models.CharField(max_length=100, null=True)
    student_content_icon_color = models.CharField(max_length=100, null=True)
    student_content_badge_color = models.CharField(max_length=100, null=True)
    student_content_background_transparent = models.CharField(max_length=100, null=True)
    student_content_background_type = models.CharField(max_length=100, null=True)
    student_content_background_color = models.CharField(max_length=100, null=True)
    student_content_background_image = models.ImageField(upload_to= student_content_background_image_directory_path, null=True)

    class Meta:
        db_table = 'users_library'

    def get_media_title(self, lang = 'en'):
        return self.media_title_en if lang == 'en' else self.media_title_ms

    def get_school_news_board_title(self, lang = 'en'):
        return self.school_news_board_title_en if lang == 'en' else self.school_news_board_title_ms

    def get_teacher_notes_title(self, lang = 'en'):
        return self.teacher_notes_title_en if lang == 'en' else self.teacher_notes_title_ms

    def get_learning_material_title(self, lang = 'en'):
        return self.learning_material_title_en if lang == 'en' else self.learning_material_title_ms

    def get_the_school_history_title(self, lang = 'en'):
        return self.the_school_history_title_en if lang == 'en' else self.the_school_history_title_ms

    def get_student_content_title(self, lang = 'en'):
        return self.student_content_title_en if lang == 'en' else self.student_content_title_ms



class Librarian(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='librarian')
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='librarians')
    storage = models.FloatField(default=10.0)

    class Meta:
        db_table = 'users_librarian'

    def delete(self, *args, **kwargs):
        self.user.delete()
        return super(self.__class__, self).delete(*args, **kwargs)


class Subscriber(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='subscriber')
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='subscribers')
    max_device = models.SmallIntegerField(default=2)
    max_borrow_duration = models.SmallIntegerField(default=10)
    max_download = models.SmallIntegerField(default=5)
    birthday = models.DateField(null=True)

    class Meta:
        db_table = 'users_subscriber'
    
    def delete(self, *args, **kwargs):
        self.user.delete()
        return super(self.__class__, self).delete(*args, **kwargs)


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher')
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='teachers')
    subject = models.CharField(max_length=50, null=True, blank= True)
    storage = models.FloatField(default=0)

    class Meta:
        db_table = 'users_teacher'
    
    def delete(self, *args, **kwargs):
        self.user.delete()
        return super(self.__class__, self).delete(*args, **kwargs)

class UserAction(models.TextChoices):
    LOGIN = 'login', _('Login')
    LOGOUT = 'logout', _('Logout')

class UsersActivity(TimeStampedModel, models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='users_activity')
    action = models.CharField(max_length=50, choices= UserAction.choices)

    class Meta:
        db_table = 'users_activity'

class Device(models.TextChoices):
    MOBILE = 'mobile', _('Mobile')
    WEB = 'web', _('Web')