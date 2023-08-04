import os
import uuid
from django.db import models
from model_utils.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _

from django.contrib.auth import get_user_model
User = get_user_model()


# Create your models here.
def school_history_directory_path(instance, filename):
    return os.path.join('school_history', "{}.{}".format(uuid.uuid4(), filename.split('.')[-1]))

class SchoolHistory(TimeStampedModel, models.Model):
    title = models.CharField(max_length=255)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_by_school_histories')
    updated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='updated_by_school_histories')
    content = models.TextField(max_length=10000000, null=True, blank=True)
    photo = models.ImageField(upload_to=school_history_directory_path, null= True)
    is_active = models.BooleanField(default=True)
    publish_date = models.DateTimeField()

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'sh_school_history'
