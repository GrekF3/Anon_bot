from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('file/<str:key>/', views.file_view, name='file_view'),
    path('upload/', views.upload_file, name='upload'),
    path('upload/success/', views.upload_success_view, name='upload_success'),
    path('download/<str:key>/', views.download_file, name='file_download'),
]