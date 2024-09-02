from django.db import models

class File(models.Model):
    FILE_TYPE_CHOICES = [
        ('image', 'Image'),
        ('file', 'File'),
        ('image_text', 'Image + Text'),
        ('video', "video")
    ]
    unique_key = models.CharField(max_length=255, unique=True)
    file = models.FileField(upload_to='files/')
    created_at = models.DateTimeField(auto_now_add=True)
    type = models.CharField(max_length=20, choices=FILE_TYPE_CHOICES)
    encryption_key = models.CharField(max_length=44)  # Ключ шифрования
    text = models.TextField(blank=True, null=True)
    chat_id = models.CharField(max_length=50, blank=True, null=True)  
    # Поле для текста (опционально)

    def __str__(self):
        return f"{self.file.name} ({self.get_type_display()})"

