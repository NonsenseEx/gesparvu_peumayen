from django.urls import path
from . import views

app_name = 'recepcion'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('asistencia/', views.registro_asistencia_view, name='registro_asistencia'),
    path('validar-qr/', views.validar_qr_view, name='validar_qr'),
]
