from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('file_manager.urls')),  # Добавьте это
    path('', include('anon_bot_manager.urls')),
    path('', include('anon_support_manager.urls'))
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
