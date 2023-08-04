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

from dateutil.relativedelta import relativedelta
from django.contrib.auth.base_user import AbstractBaseUser
from django.contrib.auth.models import PermissionsMixin, UserManager
from django.contrib.auth.validators import UnicodeUsernameValidator

from django.db import models

from click.users.models import Library, Teacher, Subscriber, User, UserType
from click.master_data.models import Category
from django.utils import timezone

from Crypto import Random
from Crypto.Cipher import AES
from shutil import copyfile
from hashlib import md5
import base64
from cryptography.fernet import Fernet


class MediaQueryset(models.QuerySet):
    def forUser(self, user):
        pass

    def active(self, is_active=True):
        return self.filter(is_active=True)

    def byCategory(self, category):
        return self.filter(category__category=category)

    def top(self):
        pass

    def lastest(self):
        return self.order_by('-id')

    def getMediaForSubscriber(self, library_id, name=None, category_id=None, media_type=None, limit=18):
        query = self.filter(library_media__library=library_id, library_media__is_active=True)

        if media_type is not None:
            query = query.filter(media_type=media_type)

        if category_id is not None:
            query = query.filter(category__category_id=category_id)

        if name is not None:
            query = query.filter(name__icontains=name)

        return query.order_by('-id')[:limit]


class FileType(models.TextChoices):
    BOOK = 'book'
    AUDIO = 'audio'
    VIDEO = 'video'
class MainCategory(models.TextChoices):
    PUBLIC = 'Public',_('Public')
    UNIVERSITY = 'University/College',_('University/College')
    SECONDARY = 'Secondary School',_('Secondary School')
    PRIMARY='Primary School',_('Primary School')
    KINDERGARTEN='Kindergarten',_('Kindergarten')


def media_file_directory_path(instance, filename):
    return os.path.join('media', 'file', 'publisher_' + str(instance.publisher_id), "{}.{}".format(uuid.uuid4(), filename.split('.')[-1]))


def media_images_directory_path(instance, filename):
    return os.path.join('media', 'images', 'media_' + str(instance.media_id), "{}.{}".format(uuid.uuid4(), filename.split('.')[-1]))


def media_preview_directory_path(instance, filename):
    return os.path.join('media', 'preview', "{}.{}".format(uuid.uuid4(), filename.split('.')[-1]))


class Media(TimeStampedModel, models.Model):
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    publisher = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    duration = models.CharField(max_length=50, null=True)
    author = models.CharField(max_length=100, null=True)
    encrypt_key = models.CharField(max_length=100, null=True)
    format_type = models.CharField(max_length=50, null=True)  # mp3, mp4, ...
    media_type = models.CharField(max_length=10, choices=FileType.choices, null=True)
    main_category=models.CharField(max_length=100, choices=MainCategory.choices, null=True,default=MainCategory.PUBLIC)
    number_of_download = models.IntegerField(default=0)
    file_size = models.IntegerField(null=True)
    url = models.FileField(upload_to=media_file_directory_path, max_length=500, null=True)
    preview_url = models.FileField(max_length=500, null=True)
    max_preview = models.IntegerField(default=5)  # queue preview
    thumbnail = models.ImageField(null=True)
    encrypt_info = models.CharField(max_length=500, null=True)
    name_encrypt = models.CharField(max_length=500, null=True)
    name_backup = models.CharField(max_length=500, null=True)
    release_date = models.DateField(null=True)
    isbn = models.CharField(max_length=50, null=True)
    price=models.FloatField(null=True,blank=True)

    objects = MediaQueryset.as_manager()

    def is_published(self):
        return timezone.now() >= self.release_date

    class Meta:
        db_table = 'media_media'
        ordering = ['name']


class MediaImage(models.Model):
    media = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=media_images_directory_path, null=True)
    thumbnail = models.ImageField(null=True)

    class Meta:
        db_table = 'media_media_image'

class RentalPeriod(models.TextChoices):
    XII='12',_('12')
    XXIV='24',_('24')
    XXXVI='36',_('36')
    XLVIII='48',_('48')


class LibraryMedia(TimeStampedModel, models.Model):
    library = models.ForeignKey(Library, on_delete=models.CASCADE, related_name='library_media')
    media = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='library_media')
    quantity = models.IntegerField()
    rental_period=models.CharField(max_length=10, choices=RentalPeriod.choices, null=True,blank=True)
    expired_date=models.DateTimeField(default=timezone.now()+relativedelta(months=12))
    number_of_download = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)
    is_renew=models.BooleanField(default=False)
    #CHECK
    media_library=models.ForeignKey('self', on_delete=models.CASCADE, related_name='old_library_media', null=True,blank=True)

    class Meta:
        db_table = 'media_library_media'


class SubscriberMedia(TimeStampedModel, models.Model):
    media = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='subscriber_media_media')
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE)
    expiration_time = models.DateTimeField()
    library_media=models.ForeignKey(LibraryMedia,  null=True,blank=True,on_delete=models.CASCADE, related_name='subscriber_library_media')

    def is_active(self):
        return timezone.now() > self.expiration_time

    class Meta:
        db_table = 'media_subscriber_media'


class SubscriberMediaAction(models.TextChoices):
    BORROW = 'borrow', _('Borrow')
    RETURN = 'return', _('Return')
    EXTEND = 'extend', _('Extend')


class SubscriberMediaTransaction(TimeStampedModel, models.Model):
    media = models.ForeignKey(Media, on_delete=models.CASCADE)
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE,related_name='media_subscriber_transactions')
    action = models.CharField(max_length=100, choices=SubscriberMediaAction.choices)

    class Meta:
        db_table = 'media_subscriber_media_transaction'


class SubscriberMediaFavorite(TimeStampedModel, models.Model):
    media = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='favorites')
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'media_subscriber_media_favorite'


class SubscriberMediaReserve(TimeStampedModel, models.Model):
    media = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='reserve')
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'media_subscriber_media_reserve'


class MediaCategory(models.Model):
    media = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='category')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='media')

    class Meta:
        db_table = 'media_media_category'

class Encryptor:
    def bytes_to_key(self, data, salt, output=48):
        assert len(salt) == 8, len(salt)
        data += salt
        key = md5(data).digest()
        final_key = key
        while len(final_key) < output:
            key = md5(key + data).digest()
            final_key += key
        return final_key[:output]

    def encrypt(self, message, key):
        salt = Random.new().read(8)
        key_iv = Encryptor.bytes_to_key(self, key, salt, 48)
        key = key_iv[:32]
        iv = key_iv[32:]
        aes = AES.new(key, AES.MODE_CBC, iv)

        BLOCK_SIZE = 16
        length = BLOCK_SIZE - (len(message) % BLOCK_SIZE)
        return base64.b64encode(b"Salted__" + salt + aes.encrypt(message + (chr(length) * length).encode()))

    def encrypt_file(self, url, file_type, key):
        key_encrypt = key.encode()
        path_src = os.path.join(settings.MEDIA_ROOT, str(url))
        filename = (str(url).split('/'))[-1]
        path_temp = os.path.join(settings.MEDIA_ROOT, 'media', 'temp', "{}.{}".format(uuid.uuid4(), filename.split('.')[-1]))
        data_enc = 80
        if file_type == FileType.AUDIO:
            data_enc = int(os.path.getsize(path_src)/10)

        with open(path_src, 'rb') as fo:
            plainttext = fo.read(data_enc)
            content = fo.read()
        plainttext = base64.b64encode(plainttext)
        enc = Encryptor.encrypt(self, plainttext, key_encrypt)
        number = "0" * (10 - len(str((len(enc))))) + str(len(enc))
        with open(path_temp, 'wb') as fo:
            fo.write(number.encode() + enc + content)
        copyfile(path_temp, path_src)
        os.remove(path_temp)

    def decrypt(self, encrypted, passphrase):
        encrypted = base64.b64decode(encrypted)
        assert encrypted[0:8] == b"Salted__"
        salt = encrypted[8:16]
        key_iv = Encryptor.bytes_to_key(self, passphrase, salt, 48)
        key = key_iv[:32]
        iv = key_iv[32:]
        aes = AES.new(key, AES.MODE_CBC, iv)
        return aes.decrypt(encrypted[16:])[: -(aes.decrypt(encrypted[16:])[-1] if type(aes.decrypt(encrypted[16:])[-1]) == int else ord(aes.decrypt(encrypted[16:])[-1]))]

    def decrypt_file(self, url, key):
        key_decrypt = key.encode()
        path_src = os.path.join(settings.MEDIA_ROOT, str(url))
        filename = (str(url).split('/'))[-1]
        path_temp = os.path.join(settings.MEDIA_ROOT, 'media', 'temp', "{}.{}".format(uuid.uuid4(), filename.split('.')[-1]))

        with open(path_src, 'rb') as fo:
            plainttext = fo.read()
        plainttext = base64.b64encode(plainttext)
        enc = Encryptor.decrypt(self, plainttext, key_decrypt)
        with open(path_temp, 'wb') as fo:
            fo.write(enc)
        copyfile(path_temp, path_src)
        os.remove(path_temp)


class Cryptography:

    def encrypt_file(self, file_name, file_type, key):
        key = base64.b64encode(key.encode())
        path_src = os.path.join(settings.MEDIA_ROOT, str(file_name))
        path_temp = os.path.join(settings.MEDIA_ROOT, 'media', 'temp', "{}.{}".format(uuid.uuid4(), str(file_name).split('.')[-1]))
        with open(path_src, 'rb') as src:
            if file_type == FileType.AUDIO:
                headers = src.read(int(os.path.getsize(path_src)/10))
            else:
                headers = src.read(80)
            content = src.read()
        encrypt_data = Fernet(key).encrypt(headers)
        number = "0" * (10 - len(str((len(encrypt_data))))) + str(len(encrypt_data))
        number = number.encode()
        with open(path_temp, 'wb') as des:
            des.write(number + encrypt_data + content)
        copyfile(path_temp, path_src)
        os.remove(path_temp)

    def decrypt_file(self, file_name, key):
        try:
            key = base64.b64encode(key.encode())
            path_src = os.path.join(settings.MEDIA_ROOT, str(file_name))
            path_temp = os.path.join(settings.MEDIA_ROOT, 'media', 'temp', "{}.{}".format(uuid.uuid4(), str(file_name).split('.')[-1]))
            with open(path_src, 'rb') as src:
                number = src.read(10)
                number = int(number.decode())
                header_encrypt = src.read(number) 
                content = src.read()
            decrypted_data = Fernet(key).decrypt(header_encrypt)
            with open(path_temp, 'wb') as des:
                des.write(decrypted_data + content)
            copyfile(path_temp, path_src)
            os.remove(path_temp) 
            # return path_temp
        except Exception as e:
            print(e)
        
