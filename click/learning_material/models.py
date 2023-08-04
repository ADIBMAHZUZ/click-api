import os
import uuid

from django.utils.translation import gettext_lazy as _
from django.db import models
from model_utils.models import TimeStampedModel
from click.media.models import MainCategory
from click.users.models import User, Library
from click.master_data.models import Category


def learning_material_file_directory_path(instance, filename):
    return os.path.join('learning_material', 'files', "{}.{}".format(uuid.uuid4(), filename.split('.')[-1]))

def learning_material_image_directory_path(instance, filename):
    return os.path.join('learning_material', 'images', "{}.{}".format(uuid.uuid4(), filename.split('.')[-1]))

class FileType(models.TextChoices):
    BOOK = 'book'
    AUDIO = 'audio'
    VIDEO = 'video'


class Media(TimeStampedModel, models.Model):
    name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    library = models.ForeignKey(Library, on_delete=models.CASCADE, null=True, related_name='learning_material_media')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, related_name='learning_material_medias')
    main_category=models.CharField(max_length=100, choices=MainCategory.choices, null=True,default=MainCategory.PUBLIC)
    duration = models.CharField(max_length=100, null=True)
    author = models.CharField(max_length=100, null=True)
    format_type = models.CharField(max_length=100, null=True)
    media_type = models.CharField(max_length= 20, choices= FileType.choices, null=True)
    number_of_download = models.IntegerField(default=0)
    file_size = models.IntegerField(null=True)
    url = models.FileField(upload_to=learning_material_file_directory_path)
    thumbnail = models.ImageField(null=True)
    release_date = models.DateTimeField(null=True)
    isbn = models.CharField(max_length=50, null=True)

    class Meta:
        db_table = 'learning_material_media'

class MediaImage(models.Model):
    media = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=learning_material_image_directory_path, null=True)
    thumbnail = models.ImageField(null=True)

    class Meta:
        db_table = 'learning_material_media_image'

class SubscriberMedia(models.Model):
    media = models.ForeignKey(Media, on_delete=models.CASCADE, related_name='learning_material_subscriber_medias')
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='learning_material_subscriber_medias')

    class Meta:
        db_table = 'learning_material_media_subscriber'

class SubscriberMediaAction(models.TextChoices):
    DOWNLOADED = 'downloaded', _('Downloaded')
    RETURN = 'return', _('Return')

class SubscriberMediaTransaction(TimeStampedModel, models.Model):
    media = models.ForeignKey(Media, on_delete= models.CASCADE, related_name= 'learning_material_media_subscriber_transactions')
    subscriber = models.ForeignKey(User, on_delete= models.CASCADE, related_name='learning_material_media_subscriber_transactions')
    action = models.CharField(choices=SubscriberMediaAction.choices, max_length= 100)

    class Meta:
        db_table = 'learning_material_media_subscriber_transaction'