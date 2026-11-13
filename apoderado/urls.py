from django.urls import path
from . import views

app_name = 'apoderado'

urlpatterns = [
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('qr/', views.generar_qr_view, name='generar_qr'),
    path('ficha/<int:parvulo_id>/', views.ficha_parvulo_view, name='ficha_parvulo'),
]
