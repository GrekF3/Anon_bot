# Используем образ Python
FROM python:3.12.3

# Отключаем буферизацию вывода Python
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Создаем необходимые директории
RUN mkdir -p $APP_HOME
RUN mkdir -p $APP_HOME/staticfiles

# Устанавливаем рабочую директорию
WORKDIR $APP_HOME

# Обновляем pip
RUN pip install --upgrade pip 

# Копируем только requirements.txt для установки зависимостей
COPY requirements.txt .

# Устанавливаем зависимости
RUN pip install -r requirements.txt

# Копируем все файлы проекта
COPY . .

# Запускаем миграции
RUN python manage.py makemigrations
