from celery import shared_task
import logging
from .models import File
from django.utils import timezone

logger = logging.getLogger(__name__)

@shared_task
def delete_expired_file():
    logger.info("Запустил задание")
    files = File.objects.all()
    for file in files:
        try:
            if file.is_expired():
                file.delete()
                logger.info(f"File {file.unique_key} has been deleted.")
            else:
                logger.info(f"File {file.unique_key} is not expired yet.")
        except File.DoesNotExist:
            logger.warning(f"File {file.unique_key} does not exist.")

@shared_task
def celery_status():
    """Выводит в консоль, что Celery запущен и работает."""
    return logger.info("Celery запущен и работает.")
