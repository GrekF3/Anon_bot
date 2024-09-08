from celery import shared_task
import logging
from .models import File
from django.utils import timezone

logger = logging.getLogger(__name__)

@shared_task
def delete_expired_file(file_id):
    logger.info(f"Запустил задание")
    try:
        file = File.objects.get(id=file_id)
        if file.is_expired():
            file.delete()
            logger.info(f"File {file_id} has been deleted.")
        else:
            logger.info(f"File {file_id} is not expired yet.")
    except File.DoesNotExist:
        logger.info(f"File {file_id} does not exist.")

@shared_task
def celery_status():
    """Выводит в консоль, что Celery запущен и работает."""
    return logger.info("Celery запущен и работает.")
