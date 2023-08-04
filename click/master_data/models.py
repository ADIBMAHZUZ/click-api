from django.db import models

# Create your models here.

class Category(models.Model):
    name = models.CharField(max_length=100)
    name_malay = models.CharField(max_length=100, null=True)
    description = models.CharField(max_length=500, null=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'master_data_category'
