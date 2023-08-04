from django.db import models
from model_utils.models import TimeStampedModel

from click.notification.models import NotificationReceiver
# Create your models here.

class Quotation(TimeStampedModel, models.Model):
    ref_no=models.CharField(max_length=200, null=True, blank=True)
    notification = models.ForeignKey(NotificationReceiver, on_delete= models.CASCADE, related_name= 'notification_quotation')