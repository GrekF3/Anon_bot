from celery import shared_task
import logging
from .models import File
from django.utils import timezone

logger = logging.getLogger(__name__)

@shared_task
def delete_expired_files():
    """Удаляет все файлы с истекшим сроком действия."""
    logger.info("Starting to delete expired files...")
    expired_files = File.objects.filter(expires_at__lt=timezone.now())
    logger.info(f"Found {expired_files.count()} expired files.")
    
    for file in expired_files:
        file.delete()  # Удаляем файл из базы данных и файловой системы
        logger.info(f"Deleted file: {file.id}")

    logger.info("Finished deleting expired files.")
