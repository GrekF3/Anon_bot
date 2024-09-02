# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.file_view, name='home'),
    path('upload/', views.upload_file, name='upload_file'),
    path('file/<str:key>/', views.download_file, name='download_file'),
]
