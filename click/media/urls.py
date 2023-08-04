from django.urls import path

from click.media import views

urlpatterns = [
    # Mobile
    path('api/media/', views.MediaList.as_view(), name='media-media'),
    path('api/media/<int:pk>/', views.MediaDetail.as_view(), name='media-media-detail'),
    path('api/media/<int:pk>/borrow/', views.MediaBorrowView.as_view(), name='media-borrow'),
    path('api/media/<int:pk>/extend/', views.MediaExtendView.as_view(), name='media-extend'),
    path('api/media/<int:pk>/return/', views.MediaReturnView.as_view(), name='media-return'),
    path('api/media/subscriber/', views.SubscriberMediaListView.as_view(), name='media-subscriber'),
    path('api/media/favorite/', views.SubscriberMediaFavoriteListView.as_view(), name='media-subscriber-favorite'),
    path('api/media/<int:pk>/favorite/', views.SubscriberMediaFavoriteListDetailView.as_view(), name='media-subscriber-favorite'),
    path('api/media/<int:pk>/related/', views.RelatedMediaView.as_view(), name='media-related'),
    path('api/media/<int:pk>/reserve/', views.ReserveMediaView.as_view(), name = 'media-reserve'),
    
    # Admin
    path('api/media_view/', views.MediaView.as_view(), name='media-views'),
    path('api/library_media_view/', views.LibraryMediaView.as_view(), name='library-media-views'),
    path('api/library_media_view/<int:pk>/', views.LibraryMediaDetailView.as_view(), name='library-media-detail-views'),
    path('api/media_view/<int:pk>/', views.MediaDetailView.as_view(), name= 'media-views-detail'),

    #Media all
    path('api/media/all/', views.GetMediaView.as_view(), name='media-views-all'),

    path('api/media/addtocart/', views.AddToCartByLibraryView.as_view(), name='media-add-to-cart'),
    path('api/media/multi_upload/', views.MultiUploadMediaView.as_view(), name = 'media-multi-upload'),

    path('api/quotation/notification/<int:pk>/',views.QuotationView.as_view(), name ='quotation'),
    #publisher
    path('api/media/<int:pk>/delete/',views.DeleteMediaView.as_view(), name ='delete-media')



    
]