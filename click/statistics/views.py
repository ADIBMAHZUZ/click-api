
from django.shortcuts import render
from click.learning_material.models import Media as Material, SubscriberMediaAction as SubscriberMaterialAction,SubscriberMediaTransaction as SubscriberMaterialTransaction
from click.media.models import Media as MediaPublisher, FileType, LibraryMedia, SubscriberMedia, SubscriberMediaTransaction,SubscriberMediaAction , SubscriberMedia
from click.users.models import User, UserType, Librarian, Subscriber
from click.users.serializers import UserSerializer
from click.master_data.models import Category
from django.utils.translation import gettext_lazy as _

from rest_framework.permissions import IsAuthenticated
from rest_framework import views, status, parsers
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, JSONParser
from django.db.models import Sum, Count,Case,When,IntegerField
from operator import itemgetter, attrgetter
from django.db.models import Q
import datetime

class NumberOfMedia(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        
        start = request.data.get('from')
        to = request.data.get('to')

        format_day = datetime.datetime.strptime(to, '%Y-%m-%d') + datetime.timedelta(days=1)
        end = datetime.datetime.strftime(format_day, '%Y-%m-%d')
        
        if request.user.is_admin():
            getUser = User.objects.filter(user_type = UserType.PUBLISHER)
            result = []

            objects = MediaPublisher.objects.filter(created__range = [start, end])
            total = objects.count()

            totalBook = objects.filter(media_type= FileType.BOOK).count()
            totalAudio = objects.filter(media_type= FileType.AUDIO).count()
            totalVideo = objects.filter(media_type= FileType.VIDEO).count()
            for publisher in getUser:
                name = publisher.short_name
                book = objects.filter(media_type= FileType.BOOK, publisher_id = publisher.id).count()
                audio = objects.filter(media_type= FileType.AUDIO, publisher_id = publisher.id).count()
                video = objects.filter(media_type= FileType.VIDEO, publisher_id = publisher.id).count()
                
                data = {'name':  name, 'book': book, 'audio': audio, 'video': video}
                result.append(data)
            numberOfMedia = {'total': total, 'book': totalBook, 'audio': totalAudio, 'video': totalVideo, 'result': result }
            return Response(numberOfMedia)        
        elif request.user.is_publisher():
            result = []

            objects = MediaPublisher.objects.filter(created__range = [start, end], publisher_id = request.user.id)
            total = objects.count()

            book = objects.filter(media_type= FileType.BOOK).count()
            audio = objects.filter(media_type= FileType.AUDIO).count()
            video = objects.filter(media_type= FileType.VIDEO).count()
            name = request.user.short_name
            
            data = {'name':  name, 'book': book, 'audio': audio, 'video': video}
            result.append(data)
            numberOfMedia = {'total': total, 'result': result }
            return Response(numberOfMedia)                                                     

class MediaPerCategory(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        
        start = request.data.get('from')
        to = request.data.get('to')

        format_day = datetime.datetime.strptime(to, '%Y-%m-%d') + datetime.timedelta(days=1)
        end = datetime.datetime.strftime(format_day, '%Y-%m-%d')

        if request.user.is_admin():
            objects = MediaPublisher.objects.filter(created__range = [start, end])
            total = objects.count()
            mediaPerCategory = {'total': total}

            getCategory = Category.objects.all()
            for category in getCategory:
                countCategory = objects.filter(category__category_id = category.id).count()
                nameCategory = category.name
                mediaPerCategory[nameCategory] = countCategory

            results = []

            getUser = User.objects.filter(user_type = UserType.PUBLISHER)
            for publisher in getUser:
                name = publisher.short_name
                percent = {'name': name}
                for category in getCategory:
                    total = objects.filter(publisher_id= publisher.id).count()
                    countMedia = objects.filter(publisher_id= publisher.id, category__category_id = category.id).count()
                    if total == 0:
                        perMedia = 0.0
                    else:
                        perMedia = countMedia * 100 / total
                    percent[category.name] = str(round(perMedia, 1)) + '% '+ category.name+'(' +str(countMedia) + ')'
            
                results.append(percent)
                
            mediaPerCategory['results'] = results
            return Response(mediaPerCategory)
        elif request.user.is_publisher():
            objects = MediaPublisher.objects.filter(created__range = [start, end], publisher_id = request.user.id)
            total = objects.count()
            mediaPerCategory = {'total': total}

            getCategory = Category.objects.all()

            results = []
            results_category = []
            result_data = []
            name = request.user.short_name
            percent = {'name': name}
            for category in getCategory:
                total = objects.filter().count()
                countMedia = objects.filter(category__category_id = category.id).count()
                if total == 0:
                    perMedia = 0.0
                else:
                    perMedia = countMedia * 100 / total
                percent[category.name] = str(round(perMedia, 1)) + '% '+ category.name + ' ('+str(countMedia) + ')'
                results_category.append(category.name)
                result_data.append(countMedia)
            results.append(percent)
            mediaPerCategory['category'] = results_category
            mediaPerCategory['data'] = result_data
            mediaPerCategory['results'] = results
            return Response(mediaPerCategory)

class SubscriberPerMedia(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        
        if request.user.is_admin():
            start = request.data.get('from')
            to = request.data.get('to')

            format_day = datetime.datetime.strptime(to, '%Y-%m-%d') + datetime.timedelta(days=1)
            end = datetime.datetime.strftime(format_day, '%Y-%m-%d')
            
            get_subscribers = User.objects.filter(created__range= [start, end], user_type = UserType.SUBSCRIBER)
            total = get_subscribers.count()
            get_librarian = User.objects.filter(user_type = UserType.LIBRARIAN)
            result_name = []
            result_count = []
            for id_librarian in get_librarian:
                count_sub = 0
                library = Librarian.objects.filter(user_id = id_librarian.id).first().library_id
                for sub in get_subscribers:
                    num_subscriber = Subscriber.objects.filter(library_id = library, user_id= sub.id).first()
                    if num_subscriber != None:
                        count_sub = count_sub + 1

                result_name.append(id_librarian.short_name)
                result_count.append(count_sub)
            subscriberPerMedia = {'total': total, 'name': result_name, 'data': result_count}
            return Response(subscriberPerMedia)
        return Response(None)

class NumberOfDownload(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        start = request.data.get('from')
        to = request.data.get('to')

        format_day = datetime.datetime.strptime(to, '%Y-%m-%d') + datetime.timedelta(days=1)
        end = datetime.datetime.strftime(format_day, '%Y-%m-%d')
        
        if request.user.is_admin():
            numberOfDownload = {'total': 0}
            result = []

            getTransaction = LibraryMedia.objects.filter(created__range= [start, end])
            for trans in getTransaction:
                media = MediaPublisher.objects.filter(id = trans.media_id).first()
                librarian = Librarian.objects.filter(library_id= trans.library_id).first()
                nameLibrary = User.objects.filter(id= librarian.user_id).first().short_name
                namePublisher = User.objects.filter(id= media.publisher_id).first().short_name
                mediaType = media.media_type

                numberOfDownload['total'] = numberOfDownload['total'] + trans.number_of_download
                if nameLibrary in numberOfDownload:
                    numberOfDownload[nameLibrary] = numberOfDownload[nameLibrary] + trans.number_of_download
                else:
                    numberOfDownload[nameLibrary] = trans.number_of_download


                check = False
                for r in result:
                    if ((r['name'] == namePublisher) and (r['library'] == nameLibrary)):
                        check = True
                        if mediaType == FileType.BOOK:
                            r['book'] = r['book'] + trans.number_of_download
                        elif mediaType == FileType.AUDIO:
                            r['audio'] = r['audio'] + trans.number_of_download
                        elif mediaType == FileType.VIDEO:
                            r['video'] = r['video'] + trans.number_of_download

                if check == False:
                    data = {'name': namePublisher, 'library': nameLibrary, 'audio': 0, 'book': 0, 'video':0}
                    if mediaType == FileType.BOOK:
                        data['book'] = data['book'] + trans.number_of_download
                    elif mediaType == FileType.AUDIO:
                        data['audio'] = data['audio'] + trans.number_of_download
                    elif mediaType == FileType.VIDEO:
                        data['video'] = data['video'] + trans.number_of_download
                    result.append(data)

            numberOfDownload['result'] = result
            return Response(numberOfDownload)
        elif request.user.is_publisher():
            numberOfDownload = {'total': 0}
            result = []
            get_media = MediaPublisher.objects.filter(publisher_id = request.user.id)
            list_media = []
            for media in get_media:
                list_media.append(media.id)
            getTransaction = LibraryMedia.objects.filter(created__range= [start, end], media_id__in = list_media)
            for trans in getTransaction:
                media = MediaPublisher.objects.filter(id = trans.media_id).first()
                librarian = Librarian.objects.filter(library_id= trans.library_id).first()
                nameLibrary = User.objects.filter(id= librarian.user_id).first().short_name
                namePublisher = request.user.short_name
                mediaType = media.media_type

                numberOfDownload['total'] = numberOfDownload['total'] + trans.number_of_download
                if nameLibrary in numberOfDownload:
                    numberOfDownload[nameLibrary] = numberOfDownload[nameLibrary] + trans.number_of_download
                else:
                    numberOfDownload[nameLibrary] = trans.number_of_download


                check = False
                for r in result:
                    if ((r['name'] == namePublisher) and (r['library'] == nameLibrary)):
                        check = True
                        if mediaType == FileType.BOOK:
                            r['book'] = r['book'] + trans.number_of_download
                        elif mediaType == FileType.AUDIO:
                            r['audio'] = r['audio'] + trans.number_of_download
                        elif mediaType == FileType.VIDEO:
                            r['video'] = r['video'] + trans.number_of_download

                if check == False:
                    data = {'name': namePublisher, 'library': nameLibrary, 'audio': 0, 'book': 0, 'video':0}
                    if mediaType == FileType.BOOK:
                        data['book'] = data['book'] + trans.number_of_download
                    elif mediaType == FileType.AUDIO:
                        data['audio'] = data['audio'] + trans.number_of_download
                    elif mediaType == FileType.VIDEO:
                        data['video'] = data['video'] + trans.number_of_download
                    result.append(data)

            numberOfDownload['result'] = result
            return Response(numberOfDownload)
        elif request.user.is_librarian():
              
            list_subscribers=User.objects.filter(user_type =UserType.SUBSCRIBER
                                    ).values('name'
                                    ).annotate(count=
                                    Count( 'learning_material_media_subscriber_transactions',filter=Q(learning_material_media_subscriber_transactions__action=SubscriberMaterialAction.DOWNLOADED)and Q(created__range= [start, end]))
                                    + Count('notes_transaction',filter=Q(notes_transaction__action=SubscriberMaterialAction.DOWNLOADED) and Q(created__range= [start, end]))
                                    + Count('media_subscriber_transactions',filter=Q(media_subscriber_transactions__action=SubscriberMediaAction.BORROW)and Q(created__range= [start, end])))

            result_temp = sorted(list_subscribers.values(), key=itemgetter('count'))
            result=[]

            for item in result_temp:
                data = {}
                data['subscriberName'] = item['name']
                data['numberOfDownloadContent'] = item['count']

                result.append(data)
            result.reverse()
            


            return Response({"success": True,"data": result})
        return Response({"success": False,"message": 'No permission'})

def myFunc(e):
    return e['numberOfDownload']

class TopDownloadMedia(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        if request.user.is_admin():
            libraryName = request.data.get('library')
            start = request.data.get('from')
            to = request.data.get('to')

            format_day = datetime.datetime.strptime(to, '%Y-%m-%d') + datetime.timedelta(days=1)
            end = datetime.datetime.strftime(format_day, '%Y-%m-%d')
            library = 'All'

            getTrans = LibraryMedia.objects.all()
            if libraryName['name'] == library:
                getTrans = getTrans.filter(created__range= [start, end]).values('media_id').order_by('media').annotate(total_number_of_download=Sum('number_of_download'))

            else:
                getLibrarian = User.objects.filter(name = libraryName['name'], user_type = UserType.LIBRARIAN)
                for lib in getLibrarian:
                    library_id = Librarian.objects.get(user_id = lib.id).library_id
                    getTrans = getTrans.filter(library_id= library_id, created__range= [start, end]).values('media_id').order_by('media').annotate(total_number_of_download=Sum('number_of_download'))
            
            topDownload = {}
            result = []
            for t in getTrans:
                data = {}
                mediaDownload = t['total_number_of_download']
                media = MediaPublisher.objects.get(id = t['media_id'])
                data['title'] = media.name
                data['numberOfDownload'] = mediaDownload
                # data['publisherName'] = request.user.short_name
                data['media_type'] = media.media_type
                result.append(data)
            result.sort(reverse= True ,key=myFunc)
            topDownload['result'] = result
            return Response(topDownload)

        elif request.user.is_publisher():
            libraryName = request.data.get('library')
            start = request.data.get('from')
            to = request.data.get('to')

            format_day = datetime.datetime.strptime(to, '%Y-%m-%d') + datetime.timedelta(days=1)
            end = datetime.datetime.strftime(format_day, '%Y-%m-%d')
            library = 'All'

            getTrans = LibraryMedia.objects.all()
            list_media = []
            get_media = MediaPublisher.objects.filter(publisher_id = request.user.id)
            for media in get_media:
                list_media.append(media.id)
            if libraryName['name'] == library:
                getTrans = getTrans.filter(created__range= [start, end], media_id__in = list_media).values('media_id').order_by('media').annotate(total_number_of_download=Sum('number_of_download'))

            else:
                getLibrarian = User.objects.filter(name = libraryName['name'], user_type = UserType.LIBRARIAN)
                for lib in getLibrarian:
                    library_id = Librarian.objects.get(user_id = lib.id).library_id
                    getTrans = getTrans.filter(library_id= library_id, created__range= [start, end], media_id__in = list_media).values('media_id').order_by('media').annotate(total_number_of_download=Sum('number_of_download'))
            topDownload = {}
            result = []
            for t in getTrans:
                data = {}
                mediaDownload = t['total_number_of_download']
                media = MediaPublisher.objects.get(id = t['media_id'])
                data['title'] = media.name
                data['numberOfDownload'] = mediaDownload
                # data['publisherName'] = request.user.short_name
                data['media_type'] = media.media_type
                result.append(data)
            result.sort(reverse= True ,key=myFunc)
            topDownload['result'] = result
            return Response(topDownload)
        elif request.user.is_librarian():
            start = request.data.get('from')
            to = request.data.get('to')

            format_day = datetime.datetime.strptime(to, '%Y-%m-%d') + datetime.timedelta(days=1)
            end = datetime.datetime.strftime(format_day, '%Y-%m-%d')

            list_materials=Material.objects.filter(library_id=request.user.librarian.library_id
                                    ).values('name'
                                    ).annotate(count=Count( 'learning_material_media_subscriber_transactions',filter=Q(learning_material_media_subscriber_transactions__action=SubscriberMaterialAction.DOWNLOADED) and Q(created__range= [start, end])))

            result_temp = sorted(list_materials.values(), key=itemgetter('count'))
            result=[]

            for item in result_temp:
                data = {}
                data['title'] = item['name']
                data['numberOfDownload'] = item['count']

                result.append(data)
            result.reverse()
            


            return Response({"success": True,"data": result})
        return Response({"success": False,"message": 'No permission'})

class Dashboard(views.APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        data = None
        if request.user.is_admin():
            user = User.objects.all()

            number_of_Publishers = user.filter(user_type = UserType.PUBLISHER).count()
            number_of_Libraries = user.filter(user_type = UserType.LIBRARIAN).count()
            number_of_Subscribers = user.filter(user_type = UserType.SUBSCRIBER).count()
            number_of_Teachers = user.filter(user_type = UserType.TEACHER).count()

            media = MediaPublisher.objects.all()

            number_of_Books = media.filter(media_type = FileType.BOOK).count()
            number_of_Audios = media.filter(media_type = FileType.AUDIO).count()
            number_of_Videos = media.filter(media_type = FileType.VIDEO).count()
        
            data = {'number_of_publishers': number_of_Publishers, 'number_of_libraries': number_of_Libraries, 'number_of_subscribers': number_of_Subscribers, 'number_of_teachers': number_of_Teachers,
            'number_of_books': number_of_Books, 'number_of_audio': number_of_Audios, 'number_of_videos': number_of_Videos}
        elif request.user.is_publisher():
            media = MediaPublisher.objects.filter(publisher_id = request.user.id)

            number_of_Books = media.filter(media_type = FileType.BOOK).count()
            number_of_Audios = media.filter(media_type = FileType.AUDIO).count()
            number_of_Videos = media.filter(media_type = FileType.VIDEO).count()

            data = {'number_of_books': number_of_Books, 'number_of_audio': number_of_Audios, 'number_of_videos': number_of_Videos}
        if request.user.is_librarian():
            media = Material.objects.all()

            borrowed_material_ids=SubscriberMaterialTransaction.objects.filter(action=SubscriberMaterialAction.DOWNLOADED).values_list('media_id',flat=True)

            number_of_Books = media.filter(media_type = FileType.BOOK, library_id=request.user.librarian.library_id,id__in=borrowed_material_ids).count()
            number_of_Audios = media.filter(media_type = FileType.AUDIO,library_id=request.user.librarian.library_id,id__in=borrowed_material_ids).count()
            number_of_Videos = media.filter(media_type = FileType.VIDEO,library_id=request.user.librarian.library_id,id__in=borrowed_material_ids).count()
        
            data = {'number_of_books': number_of_Books, 'number_of_audio': number_of_Audios, 'number_of_videos': number_of_Videos}

        return Response({"success": True,"data": data}, status=status.HTTP_200_OK)

# mobile

class DashboardActivities(views.APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if request.user.is_subscriber():
            serializer = UserSerializer(request.user, context = {'request':request}).data
            avatar = serializer["logo"]
            name = request.user.name
            name_library = User.objects.filter(librarian__library_id = request.user.subscriber.library_id).first().name

            get_day = datetime.datetime.now().strftime('%Y-%m-%d')

            media_book = SubscriberMedia.objects.filter(subscriber_id = request.user.id, expiration_time__gt = get_day, \
                media__media_type = FileType.BOOK, media__library_media__is_active= True, media__library_media__library_id = request.user.subscriber.library_id).count()
            media_audio = SubscriberMedia.objects.filter(subscriber_id = request.user.id, expiration_time__gt = get_day, \
                media__media_type = FileType.AUDIO, media__library_media__is_active= True,  media__library_media__library_id = request.user.subscriber.library_id).count()
            media_video = SubscriberMedia.objects.filter(subscriber_id = request.user.id, expiration_time__gt = get_day, \
                media__media_type = FileType.VIDEO, media__library_media__is_active= True, media__library_media__library_id = request.user.subscriber.library_id).count()

            results = {'results': {'avatar': avatar, 'name':name, 'library':name_library, 'book': media_book, 'audio': media_audio, 'video': media_video}}
            return Response(results)

    def post(self, request, format= 'json'):
        category_id = request.data.get('category')
        media_type = request.data.get('media_type')
        start = request.data.get('from')
        to = request.data.get('to')

        format_day = datetime.datetime.strptime(to, '%Y-%m-%d') + datetime.timedelta(days=1)
        end = datetime.datetime.strftime(format_day, '%Y-%m-%d')

        get_transactions = SubscriberMediaTransaction.objects.filter(created__range= [start, end], media__category__category_id = category_id, media__media_type = media_type, subscriber_id = request.user.id).order_by('-id')
        if category_id is None:
            get_transactions = SubscriberMediaTransaction.objects.filter(created__range= [start, end], media__media_type = media_type, subscriber_id = request.user.id).order_by('-id')
        
        if media_type is None:
            get_transactions = SubscriberMediaTransaction.objects.filter(created__range= [start, end], media__category__category_id = category_id, subscriber_id = request.user.id).order_by('-id')

        if category_id is None and media_type is None:
            get_transactions = SubscriberMediaTransaction.objects.filter(created__range= [start, end], subscriber_id = request.user.id).order_by('-id')

        results = []
        for transtion in get_transactions:
            media_name = MediaPublisher.objects.filter(id = transtion.media_id).first().name
            data = {'id': transtion.id, 'date': transtion.created.isoformat(), 'media': media_name, 'action': transtion.action}
            results.append(data)
        api = {'results': results}
        
        return Response(api, status= status.HTTP_200_OK)


# Library admin:
class LibraryRegisterView(views.APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        data = None
        if request.user.is_librarian():
            user = User.objects.all()
            number_of_Subscribers = user.filter(user_type = UserType.SUBSCRIBER,subscriber__library_id=request.user.librarian.library_id).count()
            number_of_Teachers = user.filter(user_type = UserType.TEACHER,teacher__library_id=request.user.librarian.library_id).count()        
            data = {'number_of_subscribers': number_of_Subscribers, 'number_of_teachers': number_of_Teachers}

            return Response({"success": True,"data": data}, status=status.HTTP_200_OK)
        return Response({"success": False,"message": 'No permission'})

class LibraryBorrowedMaterialView(views.APIView): 
    permission_classes = [IsAuthenticated]
    def post(self, request):
        data = None
        start = request.data.get('from')
        to = request.data.get('to')
        format_day = datetime.datetime.strptime(to, '%Y-%m-%d') + datetime.timedelta(days=1)
        end = datetime.datetime.strftime(format_day, '%Y-%m-%d')
        if request.user.is_librarian():
            media = LibraryMedia.objects.filter(library_id=request.user.librarian.library_id)

            borrowed_material_ids=set(SubscriberMediaTransaction.objects.filter(action=SubscriberMediaAction.BORROW).values_list('media_id',flat=True))

            number_of_Books = media.filter(media_id__in=borrowed_material_ids,media__media_type = FileType.BOOK).values('media__media_type').annotate(count=Sum("number_of_download"))
            number_of_Audios = media.filter(media__media_type = FileType.AUDIO,
            media_id__in=borrowed_material_ids).values('media_id').annotate(count=Sum("number_of_download"))
            number_of_Videos = media.filter(media__media_type = FileType.VIDEO,
            media_id__in=borrowed_material_ids).values('media_id').annotate(count=Sum("number_of_download"))
        
            data = {'number_of_books': number_of_Books[0]['count'] if number_of_Books else 0, 
                    'number_of_audio': number_of_Audios[0]['count'] if number_of_Audios else 0, 
                    'number_of_videos': number_of_Videos[0]['count'] if number_of_Videos else 0}

            return Response({"success": True,"data": data}, status=status.HTTP_200_OK)
        return Response({"success": False,"message": 'No permission'})
class TopDownloadMaterial(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        if request.user.is_librarian():     
            start = request.data.get('from')
            to = request.data.get('to')
            format_day = datetime.datetime.strptime(to, '%Y-%m-%d') + datetime.timedelta(days=1)
            end = datetime.datetime.strftime(format_day, '%Y-%m-%d')  


            getTrans = LibraryMedia.objects.filter(library_id=request.user.librarian.library_id)
            list_media = []
            for library_media in getTrans:
                list_media.append(library_media.media.id)
            list_media=set(list_media)

            getTrans = getTrans.filter(created__range= [start, end], media_id__in = list_media).values('media_id').order_by('media').annotate(total_number_of_download=Sum('number_of_download'))
            
            topDownload = {}
            result = []
            for t in getTrans:
                data = {}
                mediaDownload = t['total_number_of_download']
                media = MediaPublisher.objects.get(id = t['media_id'])
                data['title'] = media.name
                data['numberOfDownload'] = mediaDownload
                # data['publisherName'] = request.user.short_name
                data['media_type'] = media.media_type
                result.append(data)
            result.sort(reverse= True ,key=myFunc)

            return Response({"success": True,"data": result})
        return Response({"success": False,"message": 'No permission'})


class TopActiveSubscriberView(views.APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if request.user.is_librarian():
            start = request.data.get('from')
            to = request.data.get('to')
            format_day = datetime.datetime.strptime(to, '%Y-%m-%d') + datetime.timedelta(days=1)
            end = datetime.datetime.strftime(format_day, '%Y-%m-%d')
            media_type=['book','audio','video']
            list_subscribers=User.objects.filter(user_type =UserType.SUBSCRIBER,
                                                 subscriber__library = request.user.librarian.library
                                    ).values('name'
                                    ).annotate(
                                        book=
                                            # Count( 'learning_material_media_subscriber_transactions',
                                            #     filter=Q(learning_material_media_subscriber_transactions__action=SubscriberMaterialAction.DOWNLOADED) and
                                            #             Q(learning_material_media_subscriber_transactions__media__media_type=FileType.BOOK)
                                            #             and Q(created__range= [start, end])

                                            #     )
                                             Count('media_subscriber_transactions', 
                                                filter=Q(media_subscriber_transactions__action=SubscriberMediaAction.BORROW) and Q(created__range= [start, end]) and Q(media_subscriber_transactions__media__media_type=FileType.BOOK)) ,
                                        video=
                                            # Count( 'learning_material_media_subscriber_transactions',
                                            #     filter=Q(learning_material_media_subscriber_transactions__action=SubscriberMaterialAction.DOWNLOADED) and
                                            #             Q(learning_material_media_subscriber_transactions__media__media_type=FileType.VIDEO)
                                            #             and Q(created__range= [start, end]))
                                            # + 
                                            Count('media_subscriber_transactions', 
                                                filter=Q(media_subscriber_transactions__action=SubscriberMediaAction.BORROW) and Q(created__range= [start, end]) and Q(media_subscriber_transactions__media__media_type=FileType.VIDEO)) ,
                                        audio=
                                            # Count( 'learning_material_media_subscriber_transactions',
                                            #     filter=Q(learning_material_media_subscriber_transactions__action=SubscriberMaterialAction.DOWNLOADED) and
                                            #             Q(learning_material_media_subscriber_transactions__media__media_type=FileType.AUDIO)
                                            #             and Q(created__range= [start, end]))
                                            # + 
                                            Count('media_subscriber_transactions', 
                                                filter=Q(media_subscriber_transactions__action=SubscriberMediaAction.BORROW) and Q(created__range= [start, end]) and Q(media_subscriber_transactions__media__media_type=FileType.AUDIO)) ,
                                        
                                        
                                        total= Count('media_subscriber_transactions', 
                                                filter=Q(media_subscriber_transactions__action=SubscriberMediaAction.BORROW) and Q(created__range= [start, end])and Q(media_subscriber_transactions__media__media_type__in=media_type)))
                                            # Count( 'learning_material_media_subscriber_transactions', 
                                            #     filter=Q(learning_material_media_subscriber_transactions__action=SubscriberMaterialAction.DOWNLOADED)
                                            #     and Q(created__range= [start, end]))
                                            # # + Count('notes_transaction',filter=Q(notes_transaction__action=SubscriberMaterialAction.DOWNLOADED) and Q(created__range= [start, end]))
                                            # + 
                                    
          

            result_temp = sorted(list_subscribers.values(), key=itemgetter('total'))
            result=[]

            for item in result_temp:
                data = {}
                data['Subscriber'] = item['name']
                data['Total'] = item['total']
                # data['Total'] = int(item['book']) + int(item['audio']) + int(item['video'])
                data['Book'] = item['book']
                data['Audio'] = item['audio']
                data['Video'] = item['video']
                
                result.append(data)
            result.reverse()          

            return Response({"success": True,"data": result})
        return Response({"success": False,"message": 'No permission'})









