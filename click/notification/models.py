from django.db import models
from model_utils.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _

from click.users.models import Subscriber, Teacher, User
from click.media.models import LibraryMedia, Media, RentalPeriod

class NotificationType(models.TextChoices):
    REQUEST_STORAGE = 'request_storage', _('Request_storage')
    REQUEST_DELETE_SUBSCRIBER = 'request_delete_sub', _('Request_delete_sub')
    CONFIRM_DELETE_SUBSCRIBER = 'confirm_delete_sub', _('Confirm_delete_sub')
    REQUEST_DELETE_LIBRARY = 'request_delete_tea', _('Request_delete_tea')
    CONFIRM_DELETE_LIBRARY = 'confirm_delete_tea', _('Confirm_delete_tea')
    
    REQUEST_MEDIA = 'request_media', _('Request_media')
    CONFIRM_STORAGE = 'confirm_storage', _('Confirm_storage')
    CONFIRM_MEDIA = 'confirm_media', _('Confirm_media')
    CONFIRM_RENEW_MEDIA = 'confirm_renew_media', _('Confirm_renew_media')
    CONFIRM_UPLOAD = 'confirm_upload', _('Confirm_upload')
    SEND_QUOTATION='send_quotation' , _('Send_quotation')
    REQUEST_RENEW_MEDIA='request_renew_media' , _('Send_quotation')
    EXPIRED_MEDIA='expired_media',_('Expired_media')

class NotificationStatus(models.TextChoices):
    APPROVED = 'approved', _('Approved')
    PENDING = 'pending', _('Pending')
    REJECTED = 'rejected', _('Rejected')

class MessageContent(models.Model):
    message_type = models.CharField(max_length= 20, choices= NotificationType.choices)
    description = models.CharField(max_length= 255, null= True)
    message_to_producer = models.CharField(max_length= 255, null= True)
    message_to_receiver = models.CharField(max_length= 255, null= True)
    message_to_producer_malay = models.CharField(max_length= 255, null= True)
    message_to_receiver_malay = models.CharField(max_length= 255, null= True)

    class Meta:
        db_table = 'notification_message' 

class NotificationProducer(TimeStampedModel, models.Model):
    user = models.ForeignKey(User, on_delete= models.CASCADE, related_name= 'producer')

    class Meta:
        db_table = 'notification_producer'

class NotificationReceiver(TimeStampedModel, models.Model):
    user = models.ForeignKey(User, on_delete= models.CASCADE, related_name= 'receiver')
    producer = models.ForeignKey(NotificationProducer, on_delete= models.CASCADE, related_name= 'noti_receiver')
    notification_type =  models.CharField(max_length=20, choices=NotificationType.choices)
    is_active = models.BooleanField(default= False)
    message = models.ForeignKey(MessageContent, on_delete= models.CASCADE, related_name= 'receivers')

    class Meta:
        db_table = 'notification_receiver'



class RequestStorage(models.Model):
    notification = models.ForeignKey(NotificationReceiver, on_delete= models.CASCADE, related_name= 'request_storage')
    data_upgrade = models.FloatField(default= 1.0)
    status = models.CharField(max_length= 20, choices= NotificationStatus.choices)

    class Meta:
        db_table = 'notification_request_storage'



class RequestMedia(models.Model):
    notification = models.ForeignKey(NotificationReceiver, on_delete= models.CASCADE, related_name= 'request_media')
    media = models.ForeignKey(Media, on_delete= models.CASCADE, related_name= 'request_media')
    quantity = models.IntegerField(default=0)
    status = models.CharField(max_length= 20, choices= NotificationStatus.choices)
    rental_period=models.CharField(max_length=10, choices=RentalPeriod.choices, null=True,blank=True)

    class Meta:
        db_table = 'notification_request_media'
class RequestRenewMedia(models.Model):
    notification = models.ForeignKey(NotificationReceiver, on_delete= models.CASCADE, related_name= 'notification_request_new_media')
    media = models.ForeignKey(Media, on_delete= models.CASCADE, related_name= 'notification_request_new_media')
    quantity = models.IntegerField(default=0)
    status = models.CharField(max_length= 20, choices= NotificationStatus.choices)
    rental_period=models.CharField(max_length=10, choices=RentalPeriod.choices, null=True,blank=True)
    media_library=models.ForeignKey(LibraryMedia, on_delete=models.CASCADE, related_name='old_media_library', null=True,blank=True)

    class Meta:
        db_table = 'notification_request_new_media'
class ExpiredMedia(models.Model):
    notification = models.ForeignKey(NotificationReceiver, on_delete= models.CASCADE, related_name= 'notification_expired_media')
    media_library=models.ForeignKey(LibraryMedia, on_delete=models.CASCADE, related_name='expired_media_library', null=True,blank=True)
    status = models.CharField(max_length= 20, choices= NotificationStatus.choices)
    duration=models.CharField(max_length=10, null=True,blank=True)

    class Meta:
        db_table = 'notification_expired_media'

class RequestDeleteSubscriber(models.Model):
    notification = models.ForeignKey(NotificationReceiver, on_delete= models.CASCADE, related_name= 'request_delete_subscriber_notify')
    subscriber= models.CharField(max_length=20, null=True,blank=True)
    status = models.CharField(max_length= 20, choices= NotificationStatus.choices)
    class Meta:
        db_table = 'notification_request_delete_subscriber'

class ConfirmDeleteSubscriber(models.Model):
    notification = models.ForeignKey(NotificationReceiver, on_delete= models.CASCADE, related_name= 'confirm_delete_subscriber_notify')
    request = models.ForeignKey(RequestDeleteSubscriber, on_delete=models.CASCADE, related_name= 'confirm_delete_subscriber')
    status = models.CharField(max_length= 20, choices= NotificationStatus.choices)

    class Meta:
        db_table = 'notification_confirm_delete_subscriber'

class RequestDeleteLibrary(models.Model):
    notification = models.ForeignKey(NotificationReceiver, on_delete= models.CASCADE, related_name= 'request_delete_library_notify')
    library= models.CharField(max_length=20, null=True,blank=True)
    status = models.CharField(max_length= 20, choices= NotificationStatus.choices)
    class Meta:
        db_table = 'notification_request_delete_library'

class ConfirmDeleteLibrary(models.Model):
    notification = models.ForeignKey(NotificationReceiver, on_delete= models.CASCADE, related_name= 'confirm_delete_library_notify')
    request = models.ForeignKey(RequestDeleteLibrary, on_delete=models.CASCADE, related_name= 'confirm_delete_library')
    status = models.CharField(max_length= 20, choices= NotificationStatus.choices)

    class Meta:
        db_table = 'notification_confirm_delete_library'

class ConfirmStorage(models.Model):
    notification = models.ForeignKey(NotificationReceiver, on_delete= models.CASCADE, related_name= 'confirm_storage')
    request = models.ForeignKey(RequestStorage, on_delete=models.CASCADE, related_name= 'confirm_storages')
    status = models.CharField(max_length= 20, choices= NotificationStatus.choices)

    class Meta:
        db_table = 'notification_confirm_storage'

class ConfirmMedia(models.Model):
    notification = models.ForeignKey(NotificationReceiver, on_delete= models.CASCADE, related_name= 'confirm_media')
    request = models.ForeignKey(RequestMedia, on_delete=models.CASCADE, related_name= 'confirm_medias')
    # status = models.CharField(max_length= 20, choices= NotificationStatus.choices)

    class Meta:
        db_table = 'notification_confirm_media'

class ConfirmRenewMedia(models.Model):
    notification = models.ForeignKey(NotificationReceiver, on_delete= models.CASCADE, related_name= 'confirm_renew_media')
    request = models.ForeignKey(RequestRenewMedia, on_delete=models.CASCADE, related_name= 'confirm_renew_medias')
    # status = models.CharField(max_length= 20, choices= NotificationStatus.choices)

    class Meta:
        db_table = 'notification_confirm_renew_media'

class UploadType(models.TextChoices):
    MEDIA = 'media', _('Media')
    LEARNING_MATERIAL = 'learning_material', _('Learning_material')
    TEACHER_NOTES = 'teacher_notes', _('Teacher_notes')
    STUDENT_CONTENT = 'student_content', _('Student_content')
    SCHOOL_NEWS_BOARD = 'school_news_board', _('School_news_board')
    SCHOOL_HISTORY = 'school_history', _('School_history')

class ConfirmUpload(models.Model):
    receiver = models.ForeignKey(NotificationReceiver, on_delete= models.CASCADE, related_name= 'confirm_upload')
    upload_type = models.CharField(max_length= 50, choices= UploadType.choices)
    name = models.CharField(max_length= 255, null= True)
    media_type = models.CharField(max_length= 255, null= True)

    class Meta:
        db_table = 'notification_confirm_upload'

class MessageNotification(models.TextChoices):
    NOTI_LOG_PUBLISHER_REQUEST_BUY_STORAGE = 1
    NOTI_LOG_ADMIN_ACCEPT_BUY_STORAGE = 2
    NOTI_LOG_ADMIN_REJECT_BUY_STORAGE = 3
    NOTI_LIBRARY_REQUEST_BUY_MEDIA = 4
    NOTI_LOG_PUBLISHER_ACCEPT_BUY_MEDIA = 5
    LOG_PUBLISHER_REJECT_BUY_MEDIA = 6
    LOG_UPLOAD_MEDIA = 7
    LOG_UPLOAD_LEARNING_MATERIAL = 8
    LOG_UPLOAD_TEACHER_NOTES = 9
    LOG_UPLOAD_STUDENT_CONTENT = 10
    LOG_UPLOAD_SCHOOL_NEWS_BOARD = 11
    LOG_UPLOAD_SCHOOL_HISTORY = 12
    NOTI_REQUEST_DELETE_SUBSCRIBER= 13
    NOTI_REQUEST_DELETE_LIBRARY= 14
    APPROVE_DELETE_SUBSCRIBER= 15
    APPROVE_DELETE_LIBRARY= 16
    REJECT_DELETE_SUBSCRIBER= 17
    REJECT_DELETE_LIBRARY= 18
    SEND_QUOTATION=19
    REQUEST_RENEW_MEDIA=20
    CONFIRM_REQUEST_RENEW_MEDIA=21
    REJECT_REQUEST_RENEW_MEDIA=22
    EXPIRED_MEDIA=23
    


class Quotation(TimeStampedModel, models.Model):
    ref_no=models.CharField(max_length=200, null=True, blank=True)
    notification = models.ForeignKey(NotificationReceiver, on_delete= models.CASCADE, related_name= 'notification_quotation')
    total=models.FloatField(default=0)
    is_send=models.BooleanField(default=False)
    commission= models.FloatField(null=True,blank=True)

class QuotationDetail(TimeStampedModel, models.Model):
    quotation=models.ForeignKey(Quotation, on_delete= models.CASCADE, related_name= 'notification_quotation_detail')
    media=models.ForeignKey(Media,  null=True,blank=True,on_delete=models.CASCADE, related_name='quotation_media')
    price=models.FloatField(null=True,blank=True)
    quantity=models.IntegerField(default=0)
    rental_period=models.CharField(max_length=10,null=True,blank=True)


class SendQuotation(TimeStampedModel,models.Model):
    notification = models.ForeignKey(NotificationReceiver, on_delete= models.CASCADE, related_name= 'send_quotation')
    quotation= models.ForeignKey(Quotation, on_delete= models.CASCADE, related_name= 'notification_send_quotation')