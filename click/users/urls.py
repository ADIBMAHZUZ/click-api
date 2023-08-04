from django.urls import path

from click.users import views


urlpatterns = [
    path('api/auth/login/', views.LoginView.as_view(), name='auth-login'),
    path('api/auth/logout/', views.LogoutView.as_view(), name='auth-logout'),
    path('api/auth/forgot-password/', views.ForgotPasswordView.as_view(), name='auth-forgot-password'),
    path('api/auth/check-forgot-password-token/', views.CheckForgotPasswordTokenView.as_view(), name='auth-check-forgot-password-token'),
    path('api/auth/create-new-password/', views.CreateNewPasswordView.as_view(), name='auth-create-new-password'),
    path('api/auth/activate-account/', views.ActivateAccountView.as_view(), name='auth-activate-account'),

    path('api/users/change-password/', views.ChangePasswordView.as_view(), name='users-change-password'),
    path('api/users/profile/', views.ProfileView.as_view(), name='users-profile'),

    path('api/users/teachers/',views.TeacherView.as_view(), name='users-teachers'),
    path('api/users/teachers/<int:pk>/', views.TeacherDetailView.as_view(), name='users-teachers-detail'),

    path('api/users/subscribers/', views.SubscriberView.as_view(), name='users-subscribers'),
    path('api/users/subscribers/<int:pk>/', views.SubscriberDetailView.as_view(), name='users-subscribers-detail'),

    path('api/users/publishers/', views.PublisherView.as_view(), name='users-publishers'),
    path('api/users/publishers/<int:pk>/', views.PublisherDetailView.as_view(), name='users-publishers-detail'),
    path('api/users/publishers/views/', views.GetAllPublisherView.as_view(), name= 'users-publishers-all'),
    

    path('api/users/libraries/', views.LibraryView.as_view(), name= 'users-libraries'),
    path('api/users/librarians/', views.LibrarianView.as_view(), name= 'users-librarians'),
    path('api/users/librarians/<int:pk>/', views.LibrarianDetailView.as_view(), name='users-librarians-detail'),

    path('api/users/admin/', views.AdminView.as_view(), name='users-admin'),
    path('api/users/admin/<int:pk>/', views.AdminDetailView.as_view(), name='users-admin-detail'),

    path('api/users/import_subscribers/', views.ImportSubscriberView.as_view(), name= 'users-import-subscribers'),
    path('api/users/tracking_subscribers/', views.TrackingActionSubscriberView.as_view(), name= 'users-tracking-subscribers'),
    path('api/users/current_subscribers/', views.ShowCurrentSubscriberOfLibraryView.as_view(), name='current-subscribers-of-library'),
    path('api/admin/max_device/<int:pk>/', views.AdminUpdateMaxdeviceView.as_view(), name= 'admin-update-max-device'),
    path('api/users/import_teachers/', views.ImportTeacherView.as_view(), name= 'users-import-teachers'),
    path('api/subscriber/profile/', views.ProfileSubscriberView.as_view(), name= 'users-subscribers-profile'),

    # path('api/users/delete/<int:pk>/', views.UserDeleteView.as_view(), name= 'users-delete'),
    path('api/users/delete/', views.UserDeleteView.as_view(), name= 'users-delete'),

]