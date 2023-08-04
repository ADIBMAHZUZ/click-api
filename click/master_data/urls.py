from django.urls import path

from click.master_data import views

urlpatterns = [
    path('api/master_data/categories/', views.CategoryList.as_view(), name='master_data-categories'),
    path('api/master_data/categories/<int:pk>/', views.CategoryDetail.as_view(), name='master_data-categories-detail'),
]