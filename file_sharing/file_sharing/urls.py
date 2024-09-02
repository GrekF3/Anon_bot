from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('file_manager.urls')),  # Добавьте это
    path('', include('anon_bot_manager.urls')),
    path('', include('anon_support_manager.urls'))
] 
