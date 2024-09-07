from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Задаем переменную окружения для настроек Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'file_sharing.settings')

# Создаем экземпляр приложения Celery
app = Celery('file_sharing')

# Загружаем настройки из конфигурационного файла Django
app.config_from_object('django.conf:settings', namespace='CELERY')

# Автоматически находит задачи в приложениях Django
app.autodiscover_tasks()
