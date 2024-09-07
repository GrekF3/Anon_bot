# Используем образ Python
FROM python:3.12.3

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Запускаем миграции и запускаем сервер
CMD python manage.py makemigrations && python manage.py migrate && python manage.py runserver 0.0.0.0:8000
