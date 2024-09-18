from celery import shared_task
import logging
from .models import File
from django.utils import timezone
import os

logger = logging.getLogger(__name__)

@shared_task
def delete_expired_file():
    logger.info("Запустил задание")
    files = File.objects.all()
    for file in files:
        try:
            if file.is_expired():
                file.delete()
                logger.info(f"File {file.unique_key} has been deleted (expired).")
            elif file.is_opened and not file.is_downloaded and not file.expires_at:
                # Удаление одноразового файла, который был открыт, но не был скачан и не имеет срока жизни
                file.delete()
                logger.info(f"File {file.unique_key} has been deleted (one-time file).")
            else:
                logger.info(f"File {file.unique_key} is not expired or still valid.")
        except File.DoesNotExist:
            logger.warning(f"File {file.unique_key} does not exist.")

@shared_task
def delete_qr_code_file(file_path):
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Файл {file_path} успешно удалён.")
        else:
            logger.warning(f"Файл {file_path} не найден для удаления.")
    except Exception as e:
        logger.error(f"Ошибка при удалении файла {file_path}: {e}")



@shared_task
def celery_status():
    """Выводит в консоль, что Celery запущен и работает."""
    return logger.info("Celery запущен и работает.")
