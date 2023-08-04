from django.urls import path
from click.learning_material import views



urlpatterns = [
    path('api/learning_material/', views.MediaView.as_view(), name= 'learning-material'),
    path('api/learning_material/<int:pk>/', views.MediaDetailView.as_view(), name= 'learning-material-detail'),
    path('api/learning_material/get/', views.LearningMaterialUserView.as_view(), name= 'learning-material-list-by-category'),
    path('api/learning_material/get/<int:id>/', views.LearningMaterialUserDetailView.as_view(), name= 'learning-material-list-by-category'),
    path('api/learning_material/category/<int:id>/', views.LearningMaterialCategoryDetailView.as_view(), name= 'learning-material-detail-by-category'),
    path('api/learning_material/<int:id>/download/', views.MediaDownloadView.as_view(), name= 'learning-material-download'),
    path('api/learning_material/<int:id>/return/', views.MediaReturnView.as_view(), name= 'learning-material-return'),
    path('api/learning_material/downloaded/', views.LearningMaterialDownloadedView.as_view(), name='learning-material-downloaded'),
    path('api/learning_material/delete/<int:pk>/', views.LearningMaterialDeleteView.as_view(), name='learning-material-delete')
]