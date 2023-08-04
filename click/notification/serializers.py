from rest_framework import serializers
from click import notification
from click.notification.models import ConfirmDeleteLibrary, ConfirmDeleteSubscriber, ConfirmRenewMedia, ExpiredMedia, NotificationProducer, NotificationReceiver, MessageContent, Quotation, RequestDeleteSubscriber, RequestDeleteLibrary, \
RequestMedia, RequestRenewMedia, RequestStorage, NotificationType, ConfirmStorage, ConfirmMedia, NotificationStatus, SendQuotation, UploadType, ConfirmUpload
from click.users.models import Librarian, User, UserType
from click.media.models import Media

class NotificationProducerSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = NotificationProducer
        fields = ['id', 'user']
        read_only_fields = ('id',)

class QuotationSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Quotation
        fields = ['id', 'notification','is_send','ref_no']
        read_only_fields = ('id',)

class NotificationReceiverSerializer(serializers.ModelSerializer):

    class Meta:
        model = NotificationReceiver
        fields = ('id', 'producer', 'notification_type', 'message', 'is_active', 'user')
        read_only_fields = ('id',)


class NotificationToPublisherSerializer(serializers.ModelSerializer):
    time = serializers.ReadOnlyField(source = 'created')
    message = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    ref_no = serializers.SerializerMethodField()
    noti_type=serializers.SerializerMethodField()
    have_quotation=serializers.SerializerMethodField()
    is_send_quotation=serializers.SerializerMethodField()
    is_important=serializers.SerializerMethodField()

    class Meta:
        model = NotificationReceiver
        fields = ('id', 'time','message', 'status', 'is_active','ref_no','noti_type','have_quotation','is_send_quotation','is_important')

    def get_message(self, obj):
        language = self.context['request'].query_params.get('lan')
        library = User.objects.filter(producer = obj.producer).first().name
        get_message = MessageContent.objects.filter(id = obj.message_id).first()
        if obj.notification_type == NotificationType.REQUEST_MEDIA:
            request_medias = RequestMedia.objects.filter(notification = obj.id)                
                
            if language == 'ms':
                message_lan = get_message.message_to_receiver_malay
                return 'Perpustakaan ' + library + ' ' + message_lan + ' '+str(len(request_medias))+' media.'
            else:
                message_lan = get_message.message_to_receiver
                return 'Library ' + library + ' ' + message_lan +  ' '+str(len(request_medias))+' media.'
        
        elif obj.notification_type == NotificationType.REQUEST_RENEW_MEDIA:
            request_media = RequestRenewMedia.objects.filter(notification = obj.id).first()       
                
            if language == 'ms':
                message_lan = get_message.message_to_receiver_malay
                return 'Perpustakaan ' + library + ' ' + message_lan + ' media "'+ str(request_media.media.name)+'"'
            else:
                message_lan = get_message.message_to_receiver
                return 'Library ' + library + ' ' + message_lan + ' media "'+ str(request_media.media.name)+'"'
        
        elif obj.notification_type == NotificationType.CONFIRM_STORAGE:
            storage = ConfirmStorage.objects.filter(request__notification = obj).first()
            if language == 'ms':
                return get_message.message_to_receiver_malay
            else:
                return get_message.message_to_receiver
        elif obj.notification_type == NotificationType.SEND_QUOTATION:
            send_quotation= SendQuotation.objects.filter(notification = obj).first()
            if send_quotation is not None:
                if language == 'ms':
                    message_lan = get_message.message_to_receiver_malay
                    return 'Awak telah menerima sebut harga daripada administrator'
                else:
                    message_lan = get_message.message_to_receiver
                    return 'You has been received a quotation from administrator'
        return None

    def get_status(self, obj):
        if obj.notification_type == NotificationType.REQUEST_MEDIA:
            request=RequestMedia.objects.filter(notification = obj.id).first()
            if request:
                return request.status
        elif obj.notification_type == NotificationType.CONFIRM_STORAGE:
            return ConfirmStorage.objects.filter(notification = obj).first().status
        elif obj.notification_type == NotificationType.REQUEST_RENEW_MEDIA:
            request=RequestRenewMedia.objects.filter(notification = obj).first()
            if request:
                return request.status
        return None

    def get_ref_no(self, obj):
        if obj.notification_type == NotificationType.REQUEST_MEDIA or obj.notification_type == NotificationType.REQUEST_RENEW_MEDIA:
            quotation=Quotation.objects.filter(notification=obj).first()
            if quotation:
                return quotation.ref_no
        if obj.notification_type == NotificationType.SEND_QUOTATION:
            send_quotation= SendQuotation.objects.filter(notification = obj).first()
            if send_quotation:
                return send_quotation.quotation.ref_no
        return None
    def get_noti_type(self, obj):
        return obj.notification_type
    def get_have_quotation(self, obj):
        if obj.notification_type == NotificationType.SEND_QUOTATION or \
        obj.notification_type == NotificationType.REQUEST_MEDIA or\
        obj.notification_type == NotificationType.REQUEST_RENEW_MEDIA:
            return True
        return False
    def get_is_send_quotation(self, obj):
        if obj.notification_type == NotificationType.REQUEST_MEDIA or obj.notification_type == NotificationType.REQUEST_RENEW_MEDIA:
            quotation=Quotation.objects.filter(notification_id=obj.id).first()
            if quotation :
                if quotation.is_send:
                    return True
                return False
        return None
    def get_is_important(self, obj):
        if (obj.notification_type == NotificationType.REQUEST_MEDIA and obj.request_media.first().status==NotificationStatus.PENDING and obj.notification_quotation.first().is_send==False) or\
            (obj.notification_type == NotificationType.REQUEST_MEDIA and obj.request_media.first().status==NotificationStatus.PENDING and obj.notification_quotation.first().ref_no!=None) or\
            (obj.notification_type == NotificationType.REQUEST_RENEW_MEDIA and obj.notification_request_new_media.first().status==NotificationStatus.PENDING and obj.notification_quotation.first().is_send==False) or\
            (obj.notification_type == NotificationType.REQUEST_RENEW_MEDIA and obj.notification_request_new_media.first().status==NotificationStatus.PENDING and obj.notification_quotation.first().ref_no!=None) or\
            (obj.notification_type == NotificationType.SEND_QUOTATION and obj.send_quotation.first().quotation.ref_no==None):
            return True            
        return False


class NotificationToLibrarianSerializer(serializers.ModelSerializer):
    time = serializers.ReadOnlyField(source = 'created')
    message = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    ref_no = serializers.SerializerMethodField()
    noti_type=serializers.SerializerMethodField()
    have_quotation=serializers.SerializerMethodField()
    is_important=serializers.SerializerMethodField()

    class Meta:
        model = NotificationReceiver
        fields = ('id', 'time','message', 'status', 'is_active','ref_no','noti_type','have_quotation','is_important')

    def get_message(self, obj):
        language = self.context['request'].query_params.get('lan')
        get_message = MessageContent.objects.filter(id = obj.message_id).first()
        
        if obj.notification_type == NotificationType.CONFIRM_MEDIA:
            confirm_media = ConfirmMedia.objects.filter(notification = obj)
            if confirm_media is not None:
                count=len(confirm_media)
                publisher = User.objects.filter(producer__noti_receiver = obj).first().name
                if get_message.message_type=='confirm_media':
                    if language == 'ms':
                        message_lan = get_message.message_to_receiver_malay
                        return 'Awak ' + message_lan + ' Penerbit '+ publisher+  ' '+str(count)+' media.'
                    else:
                        message_lan = get_message.message_to_receiver
                        return 'You ' + message_lan + ' Publisher '+ publisher+  ' '+str(count)+' media.'
                elif get_message.message_type=='reject_media':
                    if language == 'ms':
                        message_lan = get_message.message_to_receiver_malay
                        return  'Penerbit '+ publisher+' '+ message_lan+  ' '+str(count)+' media.'
                    else:
                        message_lan = get_message.message_to_receiver
                        return 'Publisher '+ publisher+' '+ message_lan+  ' '+str(count)+' media.'
        elif obj.notification_type == NotificationType.REQUEST_STORAGE:
            request_storage = RequestStorage.objects.filter(notification = obj).first()
            producer = User.objects.filter(producer = obj.producer).first()
            if language == 'ms':
                return 'Pendidik ' + producer.name + ' '+ get_message.message_to_receiver_malay + ' ' + str(request_storage.data_upgrade) +' GB'
            else:
                return 'Educator ' + producer.name + ' '+ get_message.message_to_receiver + ' ' + str(request_storage.data_upgrade) +' GB'

        elif obj.notification_type == NotificationType.CONFIRM_RENEW_MEDIA:
            confirm_media = ConfirmRenewMedia.objects.filter(notification = obj).first()
            if confirm_media is not None:
                publisher = User.objects.filter(producer__noti_receiver = obj).first().name
                if language == 'ms':
                    message_lan = get_message.message_to_receiver_malay
                    return 'Media "' +str(confirm_media.request.media.name) +'" '+ message_lan + ' daripada penerbit '+ publisher
                else:
                    message_lan = get_message.message_to_receiver
                    return 'Media "' +str(confirm_media.request.media.name)+'" ' + message_lan + ' from publisher '+ publisher
        elif obj.notification_type == NotificationType.SEND_QUOTATION:
            send_quotation= SendQuotation.objects.filter(notification = obj).first()
            if send_quotation is not None:
                publisher = User.objects.filter(producer__noti_receiver = obj).first().name
                if language == 'ms':
                    message_lan = get_message.message_to_receiver_malay
                    return 'Awak ' + message_lan +' '+ publisher
                else:
                    message_lan = get_message.message_to_receiver
                    return 'You ' + message_lan +' '+ publisher
        elif obj.notification_type == NotificationType.CONFIRM_DELETE_LIBRARY:
            confirm_delete_library=ConfirmDeleteLibrary.objects.filter(notification = obj).first()
            if confirm_delete_library is not None:

                if language == 'ms':
                    return 'Library '+str(confirm_delete_library.request.library)+' '+ get_message.message_to_receiver_malay 
                else:
                    return 'Library '+str(confirm_delete_library.request.teacher)+' '+ get_message.message_to_receiver
        elif obj.notification_type == NotificationType.EXPIRED_MEDIA:
            expired_media=ExpiredMedia.objects.filter(notification = obj).first()
            
            if send_quotation is not None:
                if language == 'ms':
                    message_lan = get_message.message_to_receiver_malay
                    return 'Media No. '+str(expired_media.media_library_id) +' '+ message_lan +' '+ expired_media.duration+ (' weeks.' if expired_media.duration==2 else ' months.')
                else:
                    message_lan = get_message.message_to_receiver
                    return 'Media No. '+str(expired_media.media_library_id)  +' '+ message_lan +' '+ expired_media.duration+(' minggu.' if expired_media.duration==2 else ' bulan.')
        return None

    def get_status(self, obj):
        if obj.notification_type == NotificationType.REQUEST_STORAGE:
            return RequestStorage.objects.filter(notification = obj.id).first().status
        # if obj.notification_type == NotificationType.CONFIRM_MEDIA:
        #     return ConfirmMedia.objects.filter(notification = obj.id).first().status
        # if obj.notification_type == NotificationType.CONFIRM_RENEW_MEDIA:
        #     return ConfirmRenewMedia.objects.filter(notification = obj.id).first().status
        # if obj.notification_type == NotificationType.EXPIRED_MEDIA:
        #     expired_media=ExpiredMedia.objects.filter(notification = obj.id).first()
        #     if expired_media:
        #         return expired_media.status
        return None
    def get_ref_no(self, obj):
        if obj.notification_type == NotificationType.SEND_QUOTATION:
            send_quotation= SendQuotation.objects.filter(notification = obj).first()
            if send_quotation:
                return send_quotation.quotation.ref_no
        return None
    def get_noti_type(self, obj):
        return obj.notification_type
    def get_have_quotation(self, obj):
        if obj.notification_type == NotificationType.SEND_QUOTATION:
            return True
        return False
    def get_is_important(self, obj):
        if (obj.notification_type == NotificationType.SEND_QUOTATION and obj.send_quotation.first().quotation.ref_no==None) or\
            (obj.notification_type == NotificationType.REQUEST_STORAGE and obj.request_storage.first().status==NotificationStatus.PENDING):
            return True            
        return False


class NotificationToAdminSerializer(serializers.ModelSerializer):
    time = serializers.ReadOnlyField(source = 'created')
    message = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    noti_type=serializers.SerializerMethodField()
    ref_no=serializers.SerializerMethodField()
    have_quotation=serializers.SerializerMethodField()
    is_send_quotation=serializers.SerializerMethodField()
    is_important=serializers.SerializerMethodField()

    class Meta:
        model = NotificationReceiver
        fields =  ('id', 'time','message', 'status', 'is_active','noti_type','ref_no','have_quotation','is_send_quotation','is_important')

    def get_message(self, obj):
        language = self.context['request'].query_params.get('lan')
        producer = User.objects.filter(producer = obj.producer).first()
        get_message = MessageContent.objects.filter(id = obj.message_id).first()
        if obj.notification_type == NotificationType.REQUEST_STORAGE:
            request_storage = RequestStorage.objects.filter(notification = obj).first()
            if language == 'ms':
                return ('Penerbit ' if producer.user_type == UserType.PUBLISHER else 'Pustakawan') + producer.name + ' '+ get_message.message_to_receiver_malay + ' ' + str(request_storage.data_upgrade) +' GB'
            else:
                return ('Publisher ' if producer.user_type == UserType.PUBLISHER else 'Librarian') + producer.name + ' '+ get_message.message_to_receiver + ' ' + str(request_storage.data_upgrade) +' GB'

        elif obj.notification_type == NotificationType.CONFIRM_MEDIA:
            confirm_media = ConfirmMedia.objects.filter(notification = obj)
            
            library = User.objects.filter(producer__noti_receiver__id = confirm_media.first().request.notification_id).first().name
            if confirm_media is not None:
                publisher = User.objects.filter(producer__noti_receiver = obj).first().name
                    
                    
                if language == 'ms':
                    message_lan = get_message.message_to_receiver_malay
                    return 'Perpustakaan ' +library + ' ' + message_lan + ' Penerbit '+ publisher+ ' '+str(len(confirm_media))+' media.'
                else:
                    message_lan = get_message.message_to_receiver
                    return 'Library ' +library + ' ' + message_lan + ' Publisher '+ publisher+ ' '+str(len(confirm_media))+' media.'
        elif obj.notification_type == NotificationType.CONFIRM_RENEW_MEDIA:
            confirm_media = ConfirmRenewMedia.objects.filter(notification = obj).first()
            if confirm_media is not None:
                publisher = User.objects.filter(producer__noti_receiver = obj).first().name
                if language == 'ms':
                    message_lan = get_message.message_to_receiver_malay
                    return 'Media "' +str(confirm_media.request.media.name) +'" '+ message_lan + ' daripada penerbit '+ publisher
                else:
                    message_lan = get_message.message_to_receiver
                    return 'Media "' +str(confirm_media.request.media.name) +'" '+ message_lan + ' from publisher '+ publisher
        elif obj.notification_type == NotificationType.REQUEST_DELETE_LIBRARY:
            request_delete_library=RequestDeleteLibrary.objects.filter(notification = obj).first()
            if request_delete_library is not None:
                librarian=request_delete_library.notification.producer.user.name
                if language == 'ms':
                    return 'Librarian '+librarian+' '+ get_message.message_to_receiver_malay +'.'
                else:
                    return 'Librarian '+librarian+' '+ get_message.message_to_receiver+'.'
                    
        return None 

    def get_status(self, obj):
        if obj.notification_type == NotificationType.REQUEST_STORAGE:
            request= RequestStorage.objects.filter(notification = obj.id).first().status
            if request:
                return request.status
        if obj.notification_type == NotificationType.REQUEST_DELETE_LIBRARY:
            request=RequestDeleteLibrary.objects.filter(notification = obj.id).first()
            if request:
                return request.status
        # elif obj.notification_type == NotificationType.CONFIRM_MEDIA:
        #     return ConfirmMedia.objects.filter(notification = obj).first().status
        # elif obj.notification_type == NotificationType.CONFIRM_RENEW_MEDIA:
        #     return ConfirmRenewMedia.objects.filter(notification = obj).first().status
        return None
    def get_ref_no(self, obj):
        if obj.notification_type == NotificationType.CONFIRM_MEDIA or obj.notification_type == NotificationType.CONFIRM_RENEW_MEDIA:
            quotation=Quotation.objects.filter(notification=obj).first()
            if quotation:
                return quotation.ref_no
        return None
    def get_noti_type(self, obj):
        return obj.notification_type
    def get_have_quotation(self, obj):
        if obj.notification_type == NotificationType.CONFIRM_MEDIA or obj.notification_type == NotificationType.CONFIRM_RENEW_MEDIA:
            return True
        return False
    def get_is_send_quotation(self, obj):
        if obj.notification_type == NotificationType.CONFIRM_MEDIA or obj.notification_type == NotificationType.CONFIRM_RENEW_MEDIA:
            quotation=Quotation.objects.filter(notification_id=obj.id).first()
            if quotation :
                if quotation.is_send:
                    return True
                return False
        return None

    def get_is_important(self, obj):
        if (obj.notification_type == NotificationType.CONFIRM_MEDIA  and obj.notification_quotation.first()==None) or\
            (obj.notification_type == NotificationType.CONFIRM_RENEW_MEDIA  and obj.notification_quotation.first()==None) or\
            (obj.notification_type == NotificationType.REQUEST_STORAGE and obj.request_storage.first()==None) or\
            (obj.notification_type == NotificationType.REQUEST_DELETE_LIBRARY and obj.request_delete_library_notify.first()==None):
            return False   
        if (obj.notification_type == NotificationType.CONFIRM_MEDIA  and obj.notification_quotation.first().is_send==False) or\
            (obj.notification_type == NotificationType.CONFIRM_RENEW_MEDIA and obj.notification_quotation.first().is_send==False) or\
            (obj.notification_type == NotificationType.REQUEST_STORAGE and obj.request_storage.first().status==NotificationStatus.PENDING) or\
            (obj.notification_type == NotificationType.REQUEST_DELETE_LIBRARY and obj.request_delete_library_notify.first().status==NotificationStatus.PENDING):
            return True      
        return False
                



class PublisherLogSerializer(serializers.ModelSerializer):
    message = serializers.SerializerMethodField()

    class Meta:
        model = NotificationProducer
        fields = ('id', 'message')

    def get_message(self, obj):
        language = self.context['request'].query_params.get('lan')
        receiver = NotificationReceiver.objects.filter(producer = obj)
        get_message = MessageContent.objects.filter(id = receiver.first().message_id).first()
        if receiver.first().notification_type == NotificationType.REQUEST_STORAGE:
            data_upgrade = RequestStorage.objects.filter(notification = receiver.first()).first().data_upgrade
            if language == 'ms':
                return get_message.message_to_producer_malay + ' '+ str(data_upgrade) + ' GB'
            else:
                return get_message.message_to_producer + ' '+ str(data_upgrade) + ' GB'
        elif receiver.filter(notification_type =NotificationType.CONFIRM_MEDIA, user__user_type = UserType.LIBRARIAN).first() is not None:
            library = User.objects.filter(receiver = receiver.filter(notification_type= NotificationType.CONFIRM_MEDIA, user__user_type = UserType.LIBRARIAN).first()).first()
            if language == 'ms':
                return get_message.message_to_producer_malay + ' ' + library.name
            else:
                return get_message.message_to_producer + ' ' + library.name
        elif receiver.filter(notification_type =NotificationType.CONFIRM_RENEW_MEDIA, user__user_type = UserType.LIBRARIAN).first() is not None:
            library = User.objects.filter(receiver = receiver.filter(notification_type= NotificationType.CONFIRM_RENEW_MEDIA, user__user_type = UserType.LIBRARIAN).first()).first()
            if language == 'ms':
                return get_message.message_to_producer_malay + ' ' + library.name
            else:
                return get_message.message_to_producer + ' ' + library.name
        elif receiver.first().notification_type == NotificationType.CONFIRM_UPLOAD:
            confirm = ConfirmUpload.objects.filter(receiver = receiver.first(), upload_type= UploadType.MEDIA).first()
            if language == 'ms':
                return get_message.message_to_producer_malay + ' ' + confirm.name + ' ' + confirm.media_type
            else:
                return get_message.message_to_producer + ' ' + confirm.name + ' ' + confirm.media_type

class AdminLogSerializer(serializers.ModelSerializer):
    message = serializers.SerializerMethodField()

    class Meta:
        model = NotificationProducer
        fields = ('id', 'message')

    def get_message(self, obj):
        language = self.context['request'].query_params.get('lan')
        receiver = NotificationReceiver.objects.filter(producer= obj).first()
        get_message = MessageContent.objects.filter(id = receiver.message_id).first()
        if receiver.notification_type == NotificationType.CONFIRM_STORAGE:
            if language == 'ms':
                return get_message.message_to_producer_malay + ' ' +User.objects.filter(receiver__user = receiver.user).first().name
            else:
                return get_message.message_to_producer + ' ' + User.objects.filter(receiver__user = receiver.user).first().name
        elif receiver.notification_type == NotificationType.CONFIRM_UPLOAD:
            user = User.objects.filter(producer= obj ).first().name
            confirm = ConfirmUpload.objects.filter(receiver = receiver).first()
            if language == 'ms':
                if confirm.media_type is not None:
                    return user + ' ' + get_message.message_to_receiver_malay + ': nama: ' + confirm.name + ', menaip: ' + confirm.media_type
                else:
                    return user + ' ' + get_message.message_to_receiver_malay + ': nama: ' + confirm.name
            else:
                if confirm.media_type is not None:
                    return user + ' ' + get_message.message_to_receiver + ': name: ' + confirm.name + ', type: ' + confirm.media_type
                else:
                    return user + ' ' + get_message.message_to_receiver + ': name: ' + confirm.name
