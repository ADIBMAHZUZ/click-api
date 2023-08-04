from django.urls import path
from click.teacher_notes import views

urlpatterns = [
    path('api/teacher_notes/<int:id>/', views.TeacherNoteDefaultView.as_view(), name= 'teacher-note-default'),
    path('api/teacher_notes/create_folder/', views.CreateFolder.as_view(), name= 'teacher-note-create-folder'),
    path('api/teacher_notes/<int:id>/list/', views.TeacherNoteListView.as_view(), name= 'teacher-note-list'),
    path('api/teacher_notes/<int:id>/download/', views.TeacherNotesDownload.as_view(), name= 'teacher-note-download'),
    path('api/teacher_notes/<int:id>/return/', views.TeacherNotesReturn.as_view(), name= 'teacher-note-return'),
    path('api/teacher_notes/downloaded/', views.TeacherNotesDownloadedViews.as_view(), name= 'teacher-note-donwloaded'),

    #new
    path('api/notes/<int:pk>/', views.TeacherNoteView.as_view(), name= 'teacher-notes'),
    path('api/notes/upload/', views.TeacherNotesUploadViews.as_view(), name= 'teacher-notes-upload'),
    path('api/notes/download/<int:pk>/', views.SubscriberDownloadNotesView.as_view(), name= 'teacher-notes-donwload'),
    path('api/notes/return/<int:pk>/', views.SubscriberReturnNotesView.as_view(), name= 'teacher-notes-return'),
    path('api/notes/delete/<int:pk>/', views.TeacherNotesDeleteView.as_view(), name= 'teacher-notes-delete'),
    path('api/notes/multi_delete/', views.TeacherNotesMultiDeleteView.as_view(), name= 'teacher-notes-delete-multi'),
    path('api/notes/downloaded/', views.TeacherNotesTransactionViews.as_view(), name= 'teacher-notes-transaction'),
    path('api/notes/rename/<int:pk>/', views.TeacherNotesRenameViews.as_view(), name= 'teacher-notes-rename'),
]