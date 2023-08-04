from django.urls import path, include
from click.statistics import views

urlpatterns = [
    path('api/statistics/number_of_media/', views.NumberOfMedia.as_view(), name= 'number_of_media'),
    path('api/statistics/media_per_category/', views.MediaPerCategory.as_view(), name= 'media_per_category'),
    path('api/statistics/subscriber_per_media/', views.SubscriberPerMedia.as_view(), name = 'subcriber_per_media'),
    path('api/statistics/number_of_download/', views.NumberOfDownload.as_view(), name= 'number_of_download'),
    path('api/statistics/top_download_media/', views.TopDownloadMedia.as_view(), name= 'top_download_media'),
    path('api/statistics/dashboard/', views.Dashboard.as_view(), name= 'dash_board'),
    path('api/statistics/dashboard_activities/', views.DashboardActivities.as_view(), name= 'dashboard_activities'),


    #statistics Library admin:
    path('api/statistics/library/number_of_register', views.LibraryRegisterView.as_view(), name= 'number_of_register'),
    path('api/statistics/library/number_of_borrowed_material', views.LibraryBorrowedMaterialView.as_view(), name= 'number_of_register'),
    path('api/statistics/library/ranking_downloaded_material', views.TopDownloadMaterial.as_view(), name= 'ranking_downloaded_material'),
    path('api/statistics/library/ranking_active_subscriber', views.TopActiveSubscriberView.as_view(), name= 'ranking_active_subscriber'),
    

]