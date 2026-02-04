"""
URL configuration for election_project project.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('results.urls')),  # Include our app URLs
]
