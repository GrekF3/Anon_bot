# Используем базовый образ с Python 3.12.3
FROM python:3.12.3

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файл зависимостей и устанавливаем их
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Копируем проект в контейнер
COPY . /app/

# Установка переменных окружения для Django и бота
ENV PYTHONUNBUFFERED=1

# Команды для запуска могут быть определены в docker-compose.yml
