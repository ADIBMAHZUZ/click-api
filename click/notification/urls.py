from django.urls import path, include

from click.notification import views

urlpatterns = [
    path('api/publisher/request_storage/', views.RequestStorageView.as_view(), name= 'notification-request-storage'),
    path('api/publisher/notification/', views.NotificationToPublisherView.as_view(), name= 'notification-publisher'),
    path('api/librarian/notification/', views.NotificationToLibrarianView.as_view(), name= 'notification-librarian'),
    path('api/publisher/notification/<int:pk>/', views.PublisherCheckNotification.as_view(), name= 'notification-publisher-check'),
    path('api/admin/notification/', views.NotificationToAdminView.as_view(), name= 'notification-admin'),
    path('api/admin/notification/<int:pk>/', views.AdminCheckNotification.as_view(), name= 'notification-admin-check'),
    path('api/librarian/notification/<int:pk>/', views.LibrarianCheckNotification.as_view(), name= 'notification-librarian-check'),
    path('api/librarian/request_delete_subscriber/<int:pk>/', views.RequestDeleteSubscriberView.as_view(), name= 'notification-request-delete-subscriber'),
    path('api/librarian/request_delete_library/<int:pk>/', views.RequestDeleteLibraryView.as_view(), name= 'notification-request-delete-library'),
    path('api/users/log/', views.LogView.as_view(), name= 'publisher-log'),
    path('api/notification/count/', views.CountNotificationView.as_view(), name= 'count-notification'),
    path('api/expired_media/count/', views.CountExpiredMediaView.as_view(), name= 'count-notification'),
]   