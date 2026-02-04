"""
URL configuration for the results app.
"""
from django.urls import path
from . import views

app_name = 'results'

urlpatterns = [
    # Main pages
    path('', views.index, name='index'),
    path('polling-unit-results/', views.polling_unit_results, name='polling_unit_results'),
    path('lga-results/', views.lga_results, name='lga_results'),
    path('add-results/', views.add_results, name='add_results'),
    
    # API endpoints for AJAX (chained dropdowns)
    path('api/wards/<int:lga_uniqueid>/', views.api_get_wards, name='api_wards'),
    path('api/polling-units/<int:lga_uniqueid>/', views.api_get_polling_units, name='api_polling_units'),
]