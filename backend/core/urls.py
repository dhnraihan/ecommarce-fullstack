from django.urls import path
from . import views

urlpatterns = [
    path('health/', views.health_check, name='health_check'),
    path('stats/', views.site_stats, name='site_stats'),
]
