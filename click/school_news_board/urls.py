from django.urls import path

from click.school_news_board import views

urlpatterns = [
    path('api/school_news_board/', views.SchoolNewsBoardView.as_view(), name='shool-news-boards'),
    path('api/school_news_board/<int:pk>/', views.SchoolNewsBoardDetailView.as_view(), name='school-news-boards-detail'),
    path('api/school_news_board/delete/<int:pk>/', views.SchoolNewsBoardDeleteView.as_view(), name='school-new-boards-delete')
]
