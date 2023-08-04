from celery import Celery
from celery.schedules import crontab

from click.media.models import LibraryMedia, SubscriberMediaReserve, SubscriberMedia, Media, SubscriberMediaTransaction, SubscriberMediaAction
from click.notification.models import ExpiredMedia, MessageNotification, NotificationStatus, NotificationType
from click.notification.serializers import NotificationProducerSerializer, NotificationReceiverSerializer
from click.users.models import Subscriber, User, UserType
import datetime
from django.utils import timezone, dateformat
from django.conf import settings
from dateutil.relativedelta import relativedelta
from django.db.models import Q


app = Celery('click', broker=settings.RABBITMQ_URL)

@app.task
def check_reserve():

    subscriber_media = SubscriberMedia.objects.filter(Q(expiration_time__lt=timezone.now())|Q(library_media__expired_date__lt=timezone.now()))
    for media in subscriber_media:
        subscriber = Subscriber.objects.filter(user_id=media.subscriber_id).first()
        media.library_media.quantity += 1
        media.library_media.save()

        log = SubscriberMediaTransaction.objects.create(
            action=SubscriberMediaAction.RETURN, media_id=media.media_id, subscriber_id=subscriber.user_id
        )
        log.save()

        subscriber.max_download += 1
        subscriber.save()
        media.delete()

    library_media = LibraryMedia.objects.filter(quantity__gt=0, is_active=True)
    for library in library_media:
        subscriber_reserve = SubscriberMediaReserve.objects.filter(
            subscriber__subscriber__library__library_media__library_id=library.library_id, media=library.media
        ).distinct('media')
        media = SubscriberMediaReserve.objects.filter(id__in=subscriber_reserve).order_by('id').first()
        if media is not None:
            subscriber = Subscriber.objects.filter(user=media.subscriber).first()
            subscriber_media = SubscriberMedia.objects.filter(media=media.media, subscriber=media.subscriber).first()
            get_media = Media.objects.filter(id=media.media_id).first()

            get_media.number_of_download += 1
            get_media.save()

            library.quantity -= 1
            library.number_of_download += 1
            library.save()

            log = SubscriberMediaTransaction.objects.create(action=SubscriberMediaAction.BORROW, media=media.media, subscriber=subscriber.user)
            log.save()

            time_borrow = subscriber.max_borrow_duration
            expiration_time = timezone.now() + datetime.timedelta(days=time_borrow)

            if subscriber_media is None:
                subscriber_media = SubscriberMedia.objects.create(media=media.media, subscriber=subscriber.user, expiration_time=expiration_time, library_media =library)
                subscriber_media.save()
            else:
                subscriber_media.expiration_time = expiration_time
                subscriber_media.save()
            media.delete()


@app.task
def check_expired_library_media():
    get_date=timezone.now()
    library_medias=LibraryMedia.objects.filter(expired_date__in=[get_date +relativedelta(months=6),get_date
                     +relativedelta(months=3),get_date +relativedelta(months=1),get_date +relativedelta(days=14)])
    for library_media in library_medias:
        producer = NotificationProducerSerializer(data={
            'user':User.objects.filter(user_type= UserType.ADMIN).first().id,
        })
        producer.is_valid(raise_exception=True)
        noti_producer = producer.save()
        receiver = NotificationReceiverSerializer(data={
            'producer': noti_producer.id,
            'notification_type': NotificationType.EXPIRED_MEDIA,
            'message': MessageNotification.EXPIRED_MEDIA,
            'user': library_media.library.librarians.user.id
        })
        receiver.is_valid(raise_exception=True)
        noti_receiver = receiver.save()

        if (library_media.expired_date-get_date).days>14:
            r = relativedelta(library_media.expired_date, get_date)
            duration = (r.years * 12) + r.months
        duration=round(((library_media.expired_date-get_date).days)/7)       
        

        expired_media=ExpiredMedia.objects.create(notification = noti_receiver,
                        duration = duration,
                        status = NotificationStatus.APPROVED,
                        media_library_id=library_media.id
                        )
        expired_media.save()
        



