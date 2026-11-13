from django.urls import path
from . import views

app_name = 'docente'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('registrar-actividad/', views.registrar_actividad_view, name='registrar_actividad'),
]