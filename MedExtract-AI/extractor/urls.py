from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('historico/apagar/', views.clear_history, name='clear_history'),
]
