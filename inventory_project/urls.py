"""
URL configuration for inventory_project project.
"""
from django.contrib import admin
from django.urls import path, include
from inventory.views import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('', include('inventory.urls')),
]
