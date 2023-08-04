from django.urls import path

from click.school_history import views

urlpatterns = [
    path('api/school_history/', views.SchoolHistoryView.as_view(), name='school-history'),
    path('api/school_history/<int:pk>/', views.SchoolHistoryDetailView.as_view(), name='school-history-detail'),
    path('api/school_history/delete/<int:pk>/', views.SchoolHistoryDeleteView.as_view(), name='school-history-delete')
]