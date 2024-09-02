from django.urls import path
from .views import support_panel_view

urlpatterns = [
    # другие URL
    path('admin_bot/support/', support_panel_view, name='support_panel'),
]
