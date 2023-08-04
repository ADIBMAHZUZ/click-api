from django.urls import path

from click.student_content import views

urlpatterns = [
    # web
    path('api/student_content/', views.StudentContentView.as_view(), name='student_content'),
    path('api/student_content/<int:pk>/', views.StudentContentDetailView.as_view(), name='student_content-detail'),
    path('api/student_content/delete/<int:pk>/', views.DeleteStudentContentView.as_view(), name= 'student-content-delete'),

    # mobile
    path('api/student_content/mobile/', views.StudentContentMobileView.as_view(), name='student-content-mobile'),
    path('api/student_content/mobile/<int:pk>/', views.StudentContentMobileDetailView.as_view(), name='student-content-mobile-detail')
]
