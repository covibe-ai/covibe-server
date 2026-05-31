"""
URL configuration for covibe_server project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
"""
from django.contrib import admin
from django.urls import path, include
from .api_urls import urlpatterns as api_urlpatterns
from .views import healthcheck
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('healthcheck/', healthcheck, name='healthcheck'),
    path('admin/', admin.site.urls),
    path('api/v1/', include(api_urlpatterns)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

