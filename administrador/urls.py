from django.urls import path
from . import views

app_name = 'administrador'

urlpatterns = [
    path('', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('usuarios/', views.usuarios_lista_view, name='usuarios'),
    path('usuarios/nuevo/', views.usuario_crear_view, name='usuario_crear'),
    path('usuarios/<int:user_id>/editar/', views.usuario_editar_view, name='usuario_editar'),
    path('usuarios/<int:user_id>/desactivar/', views.usuario_desactivar_view, name='usuario_desactivar'),
    path('usuarios/<int:user_id>/activar/', views.usuario_activar_view, name='usuario_activar'),
    path('logout/', views.logout_view, name='logout'),
]