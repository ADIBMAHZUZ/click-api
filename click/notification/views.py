from re import L
from django.db.models import Q
from django.db.models import Sum
from rest_framework import generics, status, views
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import math
from click.learning_material.models import Media as MediaLibrary
from click.users.models import Library, Subscriber, Teacher, User, UserType, Librarian, Publisher
from click.notification.serializers import (
    NotificationProducerSerializer,
    NotificationReceiverSerializer,
    NotificationToLibrarianSerializer,
    NotificationToPublisherSerializer,
    NotificationToAdminSerializer,
    PublisherLogSerializer,
    AdminLogSerializer,
)
from click.notification.models import (
    ConfirmDeleteLibrary,
    ConfirmDeleteSubscriber,
    ConfirmRenewMedia,
    NotificationType,
    NotificationStatus,
    MessageNotification,
    Quotation,
    QuotationDetail,
    RequestDeleteSubscriber,
    RequestDeleteLibrary,
    RequestRenewMedia,
    RequestStorage,
    NotificationReceiver,
    RequestMedia,
    NotificationProducer,
    ConfirmStorage,
    ConfirmMedia,
    UploadType,
)
from click.media.models import LibraryMedia, Media
from dateutil.relativedelta import relativedelta
from django.utils import timezone

# Create your views here.
class RequestStorageView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        data = request.data.get('data')
        if request.user.is_publisher() or request.user.is_librarian() or request.user.is_teacher():

            if float(data) < 1.0:
                return Response({'success': False, 'error': 'Data invalid'}, status=status.HTTP_400_BAD_REQUEST)

            check_noti = NotificationReceiver.objects.filter(producer__user=request.user, is_active=True, notification_type=NotificationType.REQUEST_STORAGE).first()
            if check_noti is not None:
                return Response({'success': False, 'error': 'Your request is pending'})

            producer = NotificationProducerSerializer(data={'user': request.user.id})
            producer.is_valid(raise_exception=True)
            noti_producer = producer.save()

            receiver_user=None
            if request.user.is_teacher():
                library= Librarian.objects.filter(library_id=request.user.teacher.library_id).first()
                if library:
                    receiver_user=library.user_id
            else:
                receiver_user=User.objects.filter(user_type=UserType.ADMIN).first().id
            
            if receiver_user:
                receiver = NotificationReceiverSerializer(
                    data={
                        'producer': noti_producer.id,
                        'notification_type': NotificationType.REQUEST_STORAGE,
                        'message': MessageNotification.NOTI_LOG_PUBLISHER_REQUEST_BUY_STORAGE,
                        'is_active': True,
                        'user': receiver_user,
                    }
                )
                receiver.is_valid(raise_exception=True)
                noti_receiver = receiver.save()

                request_storage = RequestStorage.objects.create(notification=noti_receiver, data_upgrade=data, status=NotificationStatus.PENDING)
                request_storage.save()
                return Response({'success': True})
            return Response({'success': False})
        return Response({'success': False, 'error': 'No permission'}, status=status.HTTP_400_BAD_REQUEST)


class RequestDeleteSubscriberView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user_subscriber = kwargs['pk']
        if not request.user.is_librarian():
            return Response({'success': False, 'error': 'No permission'}, status=status.HTTP_400_BAD_REQUEST)

        subscriber = Subscriber.objects.filter(user_id=user_subscriber).first()
        library_id = request.user.librarian.library.id

        if library_id != subscriber.library_id:
            return Response({'success': False, 'error': 'No permission'}, status=status.HTTP_400_BAD_REQUEST)
        if not subscriber:
            return Response({'success': False, 'error': 'The subscriber does not exist'})

        check_noti = RequestDeleteSubscriber.objects.filter(subscriber=subscriber.id, status=NotificationStatus.PENDING).first()
        if check_noti is not None:
            return Response({'success': False, 'error': 'Your request is pending'})

        producer = NotificationProducerSerializer(data={'user': request.user.id})
        producer.is_valid(raise_exception=True)
        noti_producer = producer.save()

        receiver = NotificationReceiverSerializer(
            data={
                'producer': noti_producer.id,
                'notification_type': NotificationType.REQUEST_DELETE_SUBSCRIBER,
                'message': MessageNotification.NOTI_REQUEST_DELETE_SUBSCRIBER,
                'is_active': True,
                'user': User.objects.filter(user_type=UserType.ADMIN).first().id,
            }
        )
        receiver.is_valid(raise_exception=True)
        noti_receiver = receiver.save()
        request_delete_subscriber = RequestDeleteSubscriber.objects.create(notification=noti_receiver, subscriber=subscriber.id, status=NotificationStatus.PENDING)
        request_delete_subscriber.save()

        return Response({'success': True})


class RequestDeleteLibraryView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        library_id = kwargs['pk']
        if not request.user.is_librarian():
            return Response({'success': False, 'error': 'No permission'}, status=status.HTTP_400_BAD_REQUEST)

        library = Library.objects.filter(id=library_id).first()

        if not library:
            return Response({'success': False, 'error': 'The library does not exist'})

        check_noti = RequestDeleteLibrary.objects.filter(library=library.id, status=NotificationStatus.PENDING).first()
        if check_noti is not None:
            return Response({'success': False, 'error': 'Your request is pending'})

        producer = NotificationProducerSerializer(data={'user': request.user.id})
        producer.is_valid(raise_exception=True)
        noti_producer = producer.save()

        receiver = NotificationReceiverSerializer(
            data={
                'producer': noti_producer.id,
                'notification_type': NotificationType.REQUEST_DELETE_LIBRARY,
                'message': MessageNotification.NOTI_REQUEST_DELETE_LIBRARY,
                'is_active': True,
                'user': User.objects.filter(user_type=UserType.ADMIN).first().id,
            }
        )
        receiver.is_valid(raise_exception=True)
        noti_receiver = receiver.save()
        request_delete_library = RequestDeleteLibrary.objects.create(notification=noti_receiver, library=library.id, status=NotificationStatus.PENDING)
        request_delete_library.save()

        return Response({'success': True})


class CountNotificationView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_publisher():
            notifications = (
                NotificationReceiver.objects.filter(
                    Q(
                        user=self.request.user, 
                        notification_type=NotificationType.REQUEST_MEDIA, 
                        request_media__status=NotificationStatus.PENDING, 
                        notification_quotation__is_send=False)
                    | 
                    Q(
                        user=self.request.user, 
                        notification_type=NotificationType.REQUEST_MEDIA, 
                        request_media__status=NotificationStatus.PENDING, 
                        notification_quotation__ref_no__isnull=False)
                    | 
                    Q(
                        user=self.request.user,
                        notification_type=NotificationType.REQUEST_RENEW_MEDIA,
                        notification_request_new_media__status=NotificationStatus.PENDING,
                        notification_quotation__is_send=False,
                    )
                    | 
                    Q(
                        user=self.request.user,
                        notification_type=NotificationType.REQUEST_RENEW_MEDIA,
                        notification_request_new_media__status=NotificationStatus.PENDING,
                        notification_quotation__ref_no__isnull=False,
                    )
                    | 
                    Q(
                        user=self.request.user, notification_type=NotificationType.SEND_QUOTATION, 
                        send_quotation__quotation__ref_no__isnull=True
                    )
                )
                .distinct()
                .order_by('-id')
            )
            return Response({'success': True, 'data': notifications.count()})
        elif request.user.is_librarian():
            notifications = (
                NotificationReceiver.objects.filter(
                    Q(user=self.request.user, notification_type=NotificationType.SEND_QUOTATION, send_quotation__quotation__ref_no__isnull=True)
                    |Q(user=self.request.user, notification_type=NotificationType.REQUEST_STORAGE, request_storage__status=NotificationStatus.PENDING)
                )
                .distinct()
                .order_by('-id')
            )
            return Response({'success': True, 'data': notifications.count()})
        elif request.user.is_admin():
            notifications = (
                NotificationReceiver.objects.filter(
                    # Todo
                    Q(user=self.request.user, notification_type=NotificationType.CONFIRM_MEDIA, notification_quotation__is_send=False)
                    | Q(user=self.request.user, notification_type=NotificationType.CONFIRM_RENEW_MEDIA, notification_quotation__is_send=False)
                    # | Q(user=self.request.user, notification_type=NotificationType.CONFIRM_MEDIA, notification_quotation__ref_no__isnull=False)
                    # | Q(user=self.request.user, notification_type=NotificationType.CONFIRM_RENEW_MEDIA, notification_quotation__ref_no__isnull=False)
                    | Q(user=self.request.user, notification_type=NotificationType.REQUEST_STORAGE, request_storage__status=NotificationStatus.PENDING)
                    | Q(user=self.request.user, notification_type=NotificationType.REQUEST_DELETE_LIBRARY, request_storage__status=NotificationStatus.PENDING)
                )
                .distinct()
                .exclude(
                    Q(user=self.request.user, notification_type=NotificationType.CONFIRM_MEDIA, notification_quotation__ref_no='Free')
                    | Q(user=self.request.user, notification_type=NotificationType.CONFIRM_RENEW_MEDIA, notification_quotation__ref_no='Free')
                )
                .order_by('-id')
            )
            return Response({'success': True, 'data': notifications.count()})
        return Response({'success': False, 'Message': 'No permission.'})


class CountExpiredMediaView(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_librarian():
            # CHECK
            medias = LibraryMedia.objects.filter(library_id=request.user.librarian.library_id, expired_date__lt=timezone.now(), is_renew=False)
            return Response({'success': True, 'data': medias.count()})
        return Response({'success': False, 'Message': 'No permission.'})


class NotificationToLibrarianView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationToLibrarianSerializer

    def get_queryset(self):
        publisher = self.request.query_params.get('publisher')
        if publisher:
            return (
                NotificationReceiver.objects.filter(
                    Q(user=self.request.user, notification_type=NotificationType.CONFIRM_MEDIA, producer__user_id=publisher)
                    | Q(user=self.request.user, notification_type=NotificationType.CONFIRM_DELETE_SUBSCRIBER, producer__user_id=publisher)
                    | Q(user=self.request.user, notification_type=NotificationType.SEND_QUOTATION, producer__user_id=publisher)
                    | Q(user=self.request.user, notification_type=NotificationType.CONFIRM_RENEW_MEDIA, producer__user_id=publisher)
                    | Q(user=self.request.user, notification_type=NotificationType.EXPIRED_MEDIA, producer__user_id=publisher)
                )
                .order_by('-id')
                .distinct()
            )

        return (
            NotificationReceiver.objects.filter(
                Q(user=self.request.user, notification_type=NotificationType.CONFIRM_MEDIA)
                | Q(user=self.request.user, notification_type=NotificationType.CONFIRM_DELETE_SUBSCRIBER)
                | Q(user=self.request.user, notification_type=NotificationType.SEND_QUOTATION)
                | Q(user=self.request.user, notification_type=NotificationType.CONFIRM_RENEW_MEDIA)
                | Q(user=self.request.user, notification_type=NotificationType.EXPIRED_MEDIA)
                | Q(user=self.request.user, notification_type=NotificationType.REQUEST_STORAGE)
            )
            .order_by('-id')
            .distinct()
        )
        # return NotificationReceiver.objects.filter(Q(user= self.request.user,  notification_type= NotificationType.CONFIRM_MEDIA,producer__user__librarian__library_id= library)
        #     | Q(user= self.request.user,  notification_type= NotificationType.CONFIRM_DELETE_SUBSCRIBER,producer__user__librarian__library_id= library)
        #     | Q(user= self.request.user,  notification_type= NotificationType.CONFIRM_DELETE_LIBRARY,producer__user__librarian__library_id= library) ).order_by('-id')


class NotificationToPublisherView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationToPublisherSerializer

    def get_queryset(self):
        library = self.request.query_params.get('library')
        if library is None:
            return (
                NotificationReceiver.objects.filter(
                    Q(user=self.request.user, notification_type=NotificationType.REQUEST_MEDIA)
                    | Q(user=self.request.user, notification_type=NotificationType.CONFIRM_STORAGE)
                    | Q(user=self.request.user, notification_type=NotificationType.SEND_QUOTATION)
                    | Q(user=self.request.user, notification_type=NotificationType.REQUEST_RENEW_MEDIA)
                )
                .order_by('-id')
                .distinct()
            )
        return (
            NotificationReceiver.objects.filter(
                Q(user=self.request.user, notification_type=NotificationType.REQUEST_MEDIA, producer__user__librarian__library_id=library)
                | Q(user=self.request.user, notification_type=NotificationType.REQUEST_RENEW_MEDIA, producer__user__librarian__library_id=library)
            )
            .order_by('-id')
            .distinct()
        )


class PublisherCheckNotification(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationToPublisherSerializer

    def get_queryset(self):
        return NotificationReceiver.objects.filter(
            Q(user=self.request.user, notification_type=NotificationType.REQUEST_MEDIA, is_active=True)
            | Q(user=self.request.user, notification_type=NotificationType.REQUEST_RENEW_MEDIA, is_active=True)
        )

    def patch(self, request, *args, **kwargs):
        notification = self.get_object()
        accept = request.data.get('accept')
        librarian = User.objects.filter(producer__id=notification.producer_id).first()
        library = Librarian.objects.filter(user_id=librarian.id).first().library

        if notification.notification_type == NotificationType.REQUEST_MEDIA:
            request_medias = RequestMedia.objects.filter(notification=notification)
            if accept == True:
                for request_media in request_medias:
                    new_media = LibraryMedia.objects.create(
                        library=library,
                        media_id=request_media.media_id,
                        quantity=request_media.quantity,
                        rental_period=request_media.rental_period,
                        expired_date=timezone.now() + relativedelta(months=int(request_media.rental_period)),
                    )
                    new_media.save()

                    request_media = RequestMedia.objects.filter(notification=notification, media_id=request_media.media_id).first()

                    request_media.status = NotificationStatus.APPROVED
                    request_media.save()

                # send noti to admin

                producer = NotificationProducerSerializer(data={'user': request.user.id})
                producer.is_valid(raise_exception=True)
                noti_producer = producer.save()

                receiver = NotificationReceiverSerializer(
                    data={
                        'producer': noti_producer.id,
                        'notification_type': NotificationType.CONFIRM_MEDIA,
                        'message': MessageNotification.NOTI_LOG_PUBLISHER_ACCEPT_BUY_MEDIA,
                        'user': User.objects.filter(user_type=UserType.ADMIN).first().id,
                    }
                )
                receiver.is_valid(raise_exception=True)
                noti_receiver = receiver.save()

                # quotation from admin send to publisher
                quotation = Quotation.objects.create(notification=noti_receiver)
                total_payment = 0

                for request_media in request_medias:

                    confirm = ConfirmMedia.objects.create(
                        notification=noti_receiver,
                        request_id=request_media.id,
                        # status = NotificationStatus.APPROVED
                    )
                    confirm.save()

                    quotation_detail = QuotationDetail.objects.create(
                        quotation_id=quotation.id, media_id=request_media.media.id, quantity=request_media.quantity, price=request_media.media.price, rental_period=request_media.rental_period
                    )
                    if quotation_detail.price:
                        price = quotation_detail.price
                    else:
                        price = 0
                    total_payment += float(price) * int(quotation_detail.quantity) * int(quotation_detail.rental_period)
                quotation.total = total_payment
                if quotation.total==0:
                    quotation.ref_no="Free"
                    quotation.is_send=True
                quotation.save()

                # send noti confirm to library

                receiver_to_library = NotificationReceiverSerializer(
                    data={
                        'producer': noti_producer.id,
                        'notification_type': NotificationType.CONFIRM_MEDIA,
                        'message': MessageNotification.NOTI_LOG_PUBLISHER_ACCEPT_BUY_MEDIA,
                        'user': librarian.id,
                    }
                )
                receiver_to_library.is_valid(raise_exception=True)
                noti_lib = receiver_to_library.save()

                for request_media in request_medias:

                    confirm = ConfirmMedia.objects.create(
                        notification=noti_lib,
                        request_id=request_media.id,
                        # status = NotificationStatus.APPROVED
                    )
                    confirm.save()
            else:
                for request_media in request_medias:
                    request_media_temp = RequestMedia.objects.filter(notification=notification, media_id=request_media.media_id).first()
                    request_media_temp.status = NotificationStatus.REJECTED
                    request_media_temp.save()
                
                quotation = Quotation.objects.filter(notification=notification).first()
                quotation.is_send=True
                quotation.save()

                producer = NotificationProducerSerializer(data={'user': request.user.id})
                producer.is_valid(raise_exception=True)
                noti_producer = producer.save()

                receiver = NotificationReceiverSerializer(
                    data={
                        'producer': noti_producer.id,
                        'notification_type': NotificationType.CONFIRM_MEDIA,
                        'message': MessageNotification.LOG_PUBLISHER_REJECT_BUY_MEDIA,
                        'user': librarian.id,
                    }
                )
                receiver.is_valid(raise_exception=True)
                noti_receiver = receiver.save()

                for request_media in request_medias:

                    confirm = ConfirmMedia.objects.create(
                        notification=noti_receiver,
                        request_id=request_media.id,
                        # status = NotificationStatus.REJECTED
                    )
                    confirm.save()
            notification.is_active = False
            notification.save()
        if notification.notification_type == NotificationType.REQUEST_RENEW_MEDIA:
            request_renew_media = RequestRenewMedia.objects.filter(notification=notification).first()  
            if accept == True:
                new_media = LibraryMedia.objects.create(
                    library=library,
                    media_id=request_renew_media.media_id,
                    quantity=request_renew_media.quantity,
                    rental_period=request_renew_media.rental_period,
                    expired_date=timezone.now() + relativedelta(months=int(request_renew_media.rental_period)),
                )
                new_media.save()

                old_media_library = LibraryMedia.objects.filter(id=request_renew_media.media_library_id).first()
                old_media_library.is_active = False
                old_media_library.is_renew = True
                old_media_library.save()

                request_renew_media.status = NotificationStatus.APPROVED
                request_renew_media.save()

                producer = NotificationProducerSerializer(data={'user': request.user.id})
                producer.is_valid(raise_exception=True)
                noti_producer = producer.save()

                receiver = NotificationReceiverSerializer(
                    data={
                        'producer': noti_producer.id,
                        'notification_type': NotificationType.CONFIRM_RENEW_MEDIA,
                        'message': MessageNotification.CONFIRM_REQUEST_RENEW_MEDIA,
                        'user': User.objects.filter(user_type=UserType.ADMIN).first().id,
                    }
                )
                receiver.is_valid(raise_exception=True)
                noti_receiver = receiver.save()

                # quotation from admin send to publisher
                quotation = Quotation.objects.create(notification=noti_receiver)

                quotation_detail = QuotationDetail.objects.create(
                    quotation_id=quotation.id,
                    media_id=request_renew_media.media.id,
                    quantity=request_renew_media.quantity,
                    price=request_renew_media.media.price,
                    rental_period=request_renew_media.rental_period,
                )
                quotation.total = float(quotation_detail.price) * int(quotation_detail.quantity) * int(quotation_detail.rental_period)
                quotation.save()

                confirm = ConfirmRenewMedia.objects.create(notification=noti_receiver, request_id=request_renew_media.id)
                confirm.save()

                receiver_to_library = NotificationReceiverSerializer(
                    data={
                        'producer': noti_producer.id,
                        'notification_type': NotificationType.CONFIRM_RENEW_MEDIA,
                        'message': MessageNotification.CONFIRM_REQUEST_RENEW_MEDIA,
                        'user': librarian.id,
                    }
                )
                receiver_to_library.is_valid(raise_exception=True)
                noti_lib = receiver_to_library.save()

                confirm = ConfirmRenewMedia.objects.create(notification=noti_lib, request_id=request_renew_media.id)
                confirm.save()
            else:
                request_renew_media.status = NotificationStatus.REJECTED
                request_renew_media.save()

                quotation = Quotation.objects.filter(notification=notification).first()
                quotation.is_send=True
                quotation.save()

                producer = NotificationProducerSerializer(data={'user': request.user.id})
                producer.is_valid(raise_exception=True)
                noti_producer = producer.save()

                receiver = NotificationReceiverSerializer(
                    data={
                        'producer': noti_producer.id,
                        'notification_type': NotificationType.CONFIRM_RENEW_MEDIA,
                        'message': MessageNotification.REJECT_REQUEST_RENEW_MEDIA,
                        'user': librarian.id,
                    }
                )
                receiver.is_valid(raise_exception=True)
                noti_receiver = receiver.save()

                confirm = ConfirmRenewMedia.objects.create(notification=noti_receiver, request_id=request_renew_media.id)
                confirm.save()
            notification.is_active = False
            notification.save()
        return Response({'success': True})


class NotificationToAdminView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationToAdminSerializer

    def get_queryset(self):
        library = self.request.query_params.get('library')
        publisher = self.request.query_params.get('publisher')

        if library is None and publisher is None:
            return (
                NotificationReceiver.objects.filter(
                    Q(user=self.request.user, notification_type=NotificationType.REQUEST_STORAGE)
                    | Q(user=self.request.user, notification_type=NotificationType.CONFIRM_MEDIA)
                    | Q(user=self.request.user, notification_type=NotificationType.CONFIRM_RENEW_MEDIA)
                    | Q(user=self.request.user, notification_type=NotificationType.REQUEST_DELETE_SUBSCRIBER)
                    | Q(user=self.request.user, notification_type=NotificationType.REQUEST_DELETE_LIBRARY)
                )
                .order_by('-id')
                .distinct()
            )

        if library is None:
            return (
                NotificationReceiver.objects.filter(
                    Q(user=self.request.user, notification_type=NotificationType.REQUEST_STORAGE, producer__user_id=publisher)
                    | Q(user=self.request.user, notification_type=NotificationType.CONFIRM_MEDIA, producer__user_id=publisher)
                )
                .order_by('-id')
                .distinct()
            )

        if publisher is None:
            return (
                NotificationReceiver.objects.filter(
                    Q(user__librarian__library_id=library, notification_type=NotificationType.CONFIRM_MEDIA, confirm_media__request__status=NotificationStatus.APPROVED)
                    | Q(user__librarian__library_id=library, notification_type=NotificationType.CONFIRM_RENEW_MEDIA, confirm_renew_media__request__status=NotificationStatus.APPROVED)
                    | Q(user=self.request.user, notification_type=NotificationType.REQUEST_DELETE_SUBSCRIBER, producer__user_id=library)
                    | Q(user=self.request.user, notification_type=NotificationType.REQUEST_DELETE_LIBRARY, producer__user_id=library)
                )
                .order_by('-id')
                .distinct()
            )

        return (
            NotificationReceiver.objects.filter(
                Q(user=self.request.user, notification_type=NotificationType.REQUEST_STORAGE, producer__user_id=publisher)
                | Q(user__librarian__library_id=library, notification_type=NotificationType.CONFIRM_MEDIA, confirm_media__request__status=NotificationStatus.APPROVED)
                | Q(user__librarian__library_id=library, notification_type=NotificationType.CONFIRM_RENEW_MEDIA, confirm_renew_media__request__status=NotificationStatus.APPROVED)
                | Q(user=self.request.user, notification_type=NotificationType.REQUEST_DELETE_SUBSCRIBER, producer__user_id=library)
                | Q(user=self.request.user, notification_type=NotificationType.REQUEST_DELETE_LIBRARY, producer__user_id=library)
            )
            .order_by('-id')
            .distinct()
        )


class AdminCheckNotification(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationToAdminSerializer

    def get_queryset(self):
        return NotificationReceiver.objects.filter(
            Q(user=self.request.user, notification_type=NotificationType.REQUEST_STORAGE, is_active=True)
            | Q(user=self.request.user, notification_type=NotificationType.REQUEST_DELETE_SUBSCRIBER, is_active=True)
        )

    def patch(self, request, *args, **kwargs):

        notification_id = kwargs['pk']
        notification = NotificationReceiver.objects.filter(id=notification_id).first()
        accept = request.data.get('accept')
        get_user = User.objects.filter(producer__id=notification.producer_id).first()

        if notification.notification_type == NotificationType.REQUEST_STORAGE:
            request_storage = RequestStorage.objects.filter(notification=notification).first()
            if accept == True:
                if get_user.user_type == UserType.PUBLISHER:
                    publisher = Publisher.objects.filter(user_id=get_user.id).first()
                    publisher.storage += request_storage.data_upgrade
                    publisher.save()
                if get_user.user_type == UserType.LIBRARIAN:
                    librarian = Librarian.objects.filter(user_id=get_user.id).first()
                    librarian.storage += request_storage.data_upgrade
                    librarian.save()

                request_storage.status = NotificationStatus.APPROVED
                request_storage.save()

                producer = NotificationProducerSerializer(data={'user': request.user.id})
                producer.is_valid(raise_exception=True)
                noti_producer = producer.save()

                receiver = NotificationReceiverSerializer(
                    data={
                        'producer': noti_producer.id,
                        'notification_type': NotificationType.CONFIRM_STORAGE,
                        'message': MessageNotification.NOTI_LOG_ADMIN_ACCEPT_BUY_STORAGE,
                        'user': get_user.id,
                    }
                )
                receiver.is_valid(raise_exception=True)
                noti_receiver = receiver.save()

                confirm = ConfirmStorage.objects.create(notification=noti_receiver, request_id=request_storage.id, status=NotificationStatus.APPROVED)
                confirm.save()
            else:
                request_storage.status = NotificationStatus.REJECTED
                request_storage.save()

                producer = NotificationProducerSerializer(data={'user': request.user.id})
                producer.is_valid(raise_exception=True)
                noti_producer = producer.save()

                receiver = NotificationReceiverSerializer(
                    data={
                        'producer': noti_producer.id,
                        'notification_type': NotificationType.CONFIRM_STORAGE,
                        'message': MessageNotification.NOTI_LOG_ADMIN_REJECT_BUY_STORAGE,
                        'user': get_user.id,
                    }
                )
                receiver.is_valid(raise_exception=True)
                noti_receiver = receiver.save()

                confirm = ConfirmStorage.objects.create(notification=noti_receiver, request_id=request_storage.id, status=NotificationStatus.REJECTED)
                confirm.save()
            notification.is_active = False
            notification.save()
        elif notification.notification_type == NotificationType.REQUEST_DELETE_SUBSCRIBER:
            request_delete_subscriber = RequestDeleteSubscriber.objects.filter(notification=notification).first()
            if accept == True:
                subscriber_id = request_delete_subscriber.subscriber
                subscriber = Subscriber.objects.filter(id=subscriber_id).first()
                if not subscriber:
                    return Response({'success': False, 'message': 'The subscriber does not exists.'})
                subscriber.user.delete()
                subscriber.delete()

                request_delete_subscriber.status = NotificationStatus.APPROVED
                request_delete_subscriber.save()

                producer = NotificationProducerSerializer(data={'user': request.user.id})
                producer.is_valid(raise_exception=True)
                noti_producer = producer.save()

                receiver = NotificationReceiverSerializer(
                    data={
                        'producer': noti_producer.id,
                        'notification_type': NotificationType.CONFIRM_DELETE_SUBSCRIBER,
                        'message': MessageNotification.APPROVE_DELETE_SUBSCRIBER,
                        'user': get_user.id,
                    }
                )
                receiver.is_valid(raise_exception=True)
                noti_receiver = receiver.save()

                confirm = ConfirmDeleteSubscriber.objects.create(notification=noti_receiver, request_id=request_delete_subscriber.id, status=NotificationStatus.APPROVED)
                confirm.save()
            else:
                request_delete_subscriber.status = NotificationStatus.REJECTED
                request_delete_subscriber.save()

                producer = NotificationProducerSerializer(data={'user': request.user.id})
                producer.is_valid(raise_exception=True)
                noti_producer = producer.save()

                receiver = NotificationReceiverSerializer(
                    data={
                        'producer': noti_producer.id,
                        'notification_type': NotificationType.CONFIRM_DELETE_SUBSCRIBER,
                        'message': MessageNotification.REJECT_DELETE_SUBSCRIBER,
                        'user': get_user.id,
                    }
                )
                receiver.is_valid(raise_exception=True)
                noti_receiver = receiver.save()

                confirm = ConfirmDeleteSubscriber.objects.create(notification=noti_receiver, request_id=request_delete_subscriber.id, status=NotificationStatus.REJECTED)
                confirm.save()
            notification.is_active = False
            notification.save()

        elif notification.notification_type == NotificationType.REQUEST_DELETE_LIBRARY:
            request_delete_library = RequestDeleteLibrary.objects.filter(notification=notification).first()
            if accept == True:
                library_id = request_delete_library.library
                library = Library.objects.filter(id=library_id).first()
                if not library:
                    return Response({'success': False, 'message': 'The library does not exists.'})
                librarian=Librarian.objects.filter(library=library).first()
                User.objects.filter(id=librarian.user_id).delete()
                library.delete()
            else:
                request_delete_library.status = NotificationStatus.REJECTED
                request_delete_library.save()

                producer = NotificationProducerSerializer(data={'user': request.user.id})
                producer.is_valid(raise_exception=True)
                noti_producer = producer.save()

                receiver = NotificationReceiverSerializer(
                    data={
                        'producer': noti_producer.id,
                        'notification_type': NotificationType.CONFIRM_DELETE_LIBRARY,
                        'message': MessageNotification.REJECT_DELETE_LIBRARY,
                        'user': get_user.id,
                    }
                )
                receiver.is_valid(raise_exception=True)
                noti_receiver = receiver.save()

                confirm = ConfirmDeleteLibrary.objects.create(notification=noti_receiver, request_id=request_delete_library.id, status=NotificationStatus.REJECTED)
                confirm.save()
                notification.is_active = False
                notification.save()

        return Response({'success': True})

class LibrarianCheckNotification(generics.RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationToAdminSerializer

    def get_queryset(self):
        return NotificationReceiver.objects.filter(
            Q(user=self.request.user, notification_type=NotificationType.REQUEST_STORAGE, is_active=True)
        )

    def patch(self, request, *args, **kwargs):

        notification_id = kwargs['pk']
        notification = NotificationReceiver.objects.filter(id=notification_id).first()
        accept = request.data.get('accept')
        get_user = User.objects.filter(producer__id=notification.producer_id).first()

        if notification.notification_type == NotificationType.REQUEST_STORAGE:
            request_storage = RequestStorage.objects.filter(notification=notification).first()
            if accept == True:
                if get_user.user_type == UserType.TEACHER:
                    teacher = Teacher.objects.filter(user_id=get_user.id).first()
                    library=request.user.librarian

                    media =  MediaLibrary.objects.filter(library_id = library.library_id).aggregate(size = Sum('file_size'))
                    teacher_storage=Teacher.objects.filter(library_id = library.library_id).aggregate(storage = Sum('storage'))
                    current_storage=0
                    if media['size'] is not None :
                        current_storage += round(int(media['size']) / (math.pow(1024, 3)), 2)
                    if teacher_storage['storage'] is not None :
                        current_storage += round(teacher_storage['storage'],2)
                        
                    if request_storage.data_upgrade>(library.storage-current_storage):
                        return Response({'success': False, 'message': "Storage is higher than library's storage"})
                    teacher.storage+=request_storage.data_upgrade
                    teacher.save()
                request_storage.status = NotificationStatus.APPROVED
                request_storage.save()

                # producer = NotificationProducerSerializer(data={'user': request.user.id})
                # producer.is_valid(raise_exception=True)
                # noti_producer = producer.save()

                # receiver = NotificationReceiverSerializer(
                #     data={
                #         'producer': noti_producer.id,
                #         'notification_type': NotificationType.CONFIRM_STORAGE,
                #         'message': MessageNotification.NOTI_LOG_ADMIN_ACCEPT_BUY_STORAGE,
                #         'user': get_user.id,
                #     }
                # )
                # receiver.is_valid(raise_exception=True)
                # noti_receiver = receiver.save()

                # confirm = ConfirmStorage.objects.create(notification=noti_receiver, request_id=request_storage.id, status=NotificationStatus.APPROVED)
                # confirm.save()
            else:
                request_storage.status = NotificationStatus.REJECTED
                request_storage.save()

                # producer = NotificationProducerSerializer(data={'user': request.user.id})
                # producer.is_valid(raise_exception=True)
                # noti_producer = producer.save()

                # receiver = NotificationReceiverSerializer(
                #     data={
                #         'producer': noti_producer.id,
                #         'notification_type': NotificationType.CONFIRM_STORAGE,
                #         'message': MessageNotification.NOTI_LOG_ADMIN_REJECT_BUY_STORAGE,
                #         'user': get_user.id,
                #     }
                # )
                # receiver.is_valid(raise_exception=True)
                # noti_receiver = receiver.save()

                # confirm = ConfirmStorage.objects.create(notification=noti_receiver, request_id=request_storage.id, status=NotificationStatus.REJECTED)
                # confirm.save()
            notification.is_active = False
            notification.save()
        return Response({'success': True})

class LogView(generics.ListAPIView):
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.user.is_publisher():
            return PublisherLogSerializer
        elif self.request.user.is_admin():
            return AdminLogSerializer

    def get_queryset(self):
        if self.request.user.is_publisher():
            library = self.request.query_params.get('library')
            if library is not None:
                return NotificationProducer.objects.filter(
                    user=self.request.user, noti_receiver__notification_type=NotificationType.CONFIRM_MEDIA, noti_receiver__user__librarian__library_id=library
                ).order_by('-id')

            query = Q(user=self.request.user, noti_receiver__notification_type=NotificationType.CONFIRM_MEDIA, noti_receiver__user__user_type=UserType.LIBRARIAN)
            query.add(Q(user=self.request.user, noti_receiver__confirm_upload__upload_type=UploadType.MEDIA), Q.OR)
            query.add(Q(user=self.request.user, noti_receiver__notification_type=NotificationType.REQUEST_STORAGE), Q.OR)
            return NotificationProducer.objects.filter(query).order_by('-id')

        if self.request.user.is_admin():
            library = self.request.query_params.get('library')
            publisher = self.request.query_params.get('publisher')
            if publisher is None and library is None:

                query = Q(user=self.request.user, noti_receiver__notification_type=NotificationType.REQUEST_STORAGE)
                query.add(Q(noti_receiver__user=self.request.user, noti_receiver__notification_type=NotificationType.CONFIRM_UPLOAD), Q.OR)
                query.add(Q(noti_receiver__user=self.request.user, noti_receiver__notification_type=NotificationType.REQUEST_DELETE_SUBSCRIBER), Q.OR)
                query.add(Q(noti_receiver__user=self.request.user, noti_receiver__notification_type=NotificationType.REQUEST_DELETE_LIBRARY), Q.OR)
                query.add(
                    ~Q(noti_receiver__user=self.request.user, noti_receiver__notification_type=NotificationType.CONFIRM_UPLOAD, noti_receiver__confirm_upload__upload_type=UploadType.MEDIA), Q.AND
                )
                return NotificationProducer.objects.filter(query).order_by('-id')

            if publisher is None:
                return NotificationProducer.objects.filter(
                    Q(noti_receiver__user=self.request.user, noti_receiver__notification_type=NotificationType.CONFIRM_UPLOAD, user__librarian__library_id=library)
                    | Q(user=self.request.user, noti_receiver__notification_type=NotificationType.CONFIRM_DELETE_LIBRARY)
                    | Q(user=self.request.user, noti_receiver__notification_type=NotificationType.CONFIRM_DELETE_SUBSCRIBER)
                ).order_by('-id')

            if library is None:
                return NotificationProducer.objects.filter(Q(user=self.request.user, noti_receiver__notification_type=NotificationType.CONFIRM_STORAGE, noti_receiver__user_id=publisher)).order_by(
                    '-id'
                )

            query = Q(noti_receiver__user=self.request.user, noti_receiver__notification_type=NotificationType.CONFIRM_UPLOAD, user__librarian__library_id=library)
            query.add(Q(user=self.request.user, noti_receiver__notification_type=NotificationType.CONFIRM_STORAGE, noti_receiver__user_id=publisher), Q.OR)
            return NotificationProducer.objects.filter(query).order_by('-id')

        if self.request.user.is_librarian():

            return NotificationReceiver.objects.filter(
                Q(user=self.request.user, notification_type=NotificationType.CONFIRM_MEDIA)
                | Q(user=self.request.user, notification_type=NotificationType.CONFIRM_DELETE_SUBSCRIBER)
                | Q(user=self.request.user, notification_type=NotificationType.CONFIRM_DELETE_LIBRARY)
            ).order_by('-id')
