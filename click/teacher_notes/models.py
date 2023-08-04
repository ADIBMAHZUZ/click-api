from django.db import models
from click.users.models import User
from model_utils.models import TimeStampedModel
from django.utils.translation import gettext_lazy as _


class NotesDownloaded(models.Model):
    name = models.CharField(max_length=200)
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teacher_notes_subscriber')
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teacher_notes_teacher')
    size = models.CharField(max_length=100, null= True)
    file_type = models.CharField(max_length=50)
    url = models.CharField(max_length= 200)
    created_date = models.CharField(max_length=100)

    class Meta:
        db_table = 'teacher_notes_subscriber_downloaded'

class SubscriberAction(models.TextChoices):
    DOWNLOADED = 'downloaded', _('Downloaded')
    RETURN = 'return', _('Return')

class TeacherNotesAction(TimeStampedModel, models.Model):
    name = models.CharField(max_length=200)
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teacher_notes_subscriber_action')
    url = models.CharField(max_length= 200)
    action = models.CharField(choices= SubscriberAction.choices, max_length=50)

    class Meta:
        db_table = 'teacher_notes_subscriber_action'


# new
class FileType(models.TextChoices):
    FOLDER = 'folder', _('Folder')
    FILE = 'file', _('File')

class TeacherNotes(TimeStampedModel, models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teacher_notes')
    name = models.CharField(max_length= 200)
    size = models.IntegerField(default=0)
    file_type = models.CharField(max_length= 30)
    url = models.CharField(max_length= 10000)
    parent_folder = models.IntegerField(default=0)

    class Meta:
        db_table = 'teacher_notes'

class SubscriberTransaction(models.TextChoices):
    DOWNLOADED = 'downloaded', _('Downloaded')
    RETURNED = 'returned', _('Returned')

class TeacherNotesTransaction(TimeStampedModel, models.Model):
    note = models.ForeignKey(TeacherNotes, on_delete=models.CASCADE, related_name='notes_transaction')
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes_transaction')
    action = models.CharField(choices= SubscriberTransaction.choices, max_length= 20)

    class Meta:
        db_table = 'teacher_notes_transaction'

class TeacherNotesDownloaded(models.Model):
    note = models.ForeignKey(TeacherNotes, on_delete=models.CASCADE, related_name='notes_downloaded')
    subscriber = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notes_downloaded')

    class Meta:
        db_table = 'teacher_notes_downloaded'
    