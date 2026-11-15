from django.contrib.auth import views as auth_views
from django.urls import path, reverse_lazy

from . import views
from .forms import PasswordResetRequestForm, PasswordResetSetForm

app_name = 'administrador'

urlpatterns = [
    path('', views.landing_view, name='landing'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),

    # Recuperación de contraseña
    path(
        'password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='administrador/password_reset_form.html',
            email_template_name='administrador/password_reset_email.html',
            subject_template_name='administrador/password_reset_subject.txt',
            form_class=PasswordResetRequestForm,
            success_url=reverse_lazy('administrador:password_reset_done'),
        ),
        name='password_reset',
    ),
    path(
        'password-reset/enviado/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='administrador/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path(
        'password-reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='administrador/password_reset_confirm.html',
            form_class=PasswordResetSetForm,
            success_url=reverse_lazy('administrador:password_reset_complete'),
        ),
        name='password_reset_confirm',
    ),
    path(
        'password-reset/completado/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='administrador/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('usuarios/', views.usuarios_lista_view, name='usuarios'),
    path('usuarios/nuevo/', views.usuario_crear_view, name='usuario_crear'),
    path('usuarios/<int:user_id>/editar/', views.usuario_editar_view, name='usuario_editar'),
    path('usuarios/<int:user_id>/desactivar/', views.usuario_desactivar_view, name='usuario_desactivar'),
    path('usuarios/<int:user_id>/activar/', views.usuario_activar_view, name='usuario_activar'),
    path('parvulos/', views.parvulos_lista_view, name='parvulos'),
    path('parvulos/nuevo/', views.parvulo_crear_view, name='parvulo_crear'),
    path('parvulos/<int:parvulo_id>/editar/', views.parvulo_editar_view, name='parvulo_editar'),
    path('logout/', views.logout_view, name='logout'),
]