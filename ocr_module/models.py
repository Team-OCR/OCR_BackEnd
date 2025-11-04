from django.db import models

class UploadedFile(models.Model):
    original_name = models.CharField(max_length=255)
    stored_name   = models.CharField(max_length=255, unique=True)
    file          = models.FileField(upload_to='')   # we save manually
    uploaded_at   = models.DateTimeField(auto_now_add=True)
    size          = models.PositiveIntegerField()   # bytes

    def __str__(self):
        return self.original_name