from django.db import models

class File(models.Model):
    FILE_TYPE_CHOICES = [
        ('image', 'Image'),
        ('file', 'File'),
        ('image_text', 'Image + Text'),
        ('video', "Video"),
    ]
    unique_key = models.CharField(max_length=255, unique=True)
    file = models.FileField(upload_to='files/')
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    encryption_key = models.CharField(max_length=44)  # Ключ шифрования
    text = models.TextField(blank=True, null=True)
    is_downloaded = models.BooleanField(default=False) 
    mime_type = models.CharField(max_length=50, blank=True, null=True)  # Новое поле для хранения MIME-типа

    def __str__(self):
        return f"{self.file.name} ({self.get_type_display()})"