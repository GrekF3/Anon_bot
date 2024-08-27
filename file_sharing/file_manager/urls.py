# urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.file_view, name='home'),
    path('upload/', views.upload_file, name='upload_file'),
    path('file/<str:key>/', views.download_file, name='download_file'),
    path('bot_admin_page/', views.bot_admin_panel, name='bot_admin_page'),
    path('bot_admin_page/broadcast/', views.broadcast_view, name='broadcast'),
    path('bot_admin_page/manage-users/', views.manage_users_view, name='manage_users'),
    path('bot_admin_page/statistics/', views.statistics_view, name='statistics'),

]
