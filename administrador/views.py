from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.urls import reverse
from django.views.decorators.http import require_POST
from .models import Usuario
from .forms import (
    RegistroApoderadoForm,
    UsuarioAdminCreateForm,
    UsuarioAdminUpdateForm,
)
from .mixins import rol_requerido
from .validators import formatear_rut
# Importa tus modelos reales si los necesitas en otras vistas:
# from .models import Parvulo, Sala, Personal


ROLES_GESTIONADOS = [
    Usuario.Roles.DOCENTE,
    Usuario.Roles.APODERADO,
    Usuario.Roles.RECEPCION,
]


def redireccion_por_rol(user):
    """Devuelve la URL del panel principal según el rol del usuario."""
    if user.is_superuser or user.rol == Usuario.Roles.ADMINISTRADOR:
        return reverse('administrador:dashboard')
    if user.rol == Usuario.Roles.APODERADO or hasattr(user, 'perfil_apoderado'):
        return reverse('apoderado:dashboard')
    if user.rol == Usuario.Roles.DOCENTE:
        return reverse('docente:dashboard')
    if user.rol == Usuario.Roles.RECEPCION:
        return reverse('recepcion:dashboard')
    return reverse('administrador:dashboard')


def login_view(request):
    """Maneja la autenticación de usuarios."""
    if request.user.is_authenticated:
        return redirect(redireccion_por_rol(request.user))

    if request.method == 'POST':
        # Procesamiento del formulario de inicio de sesión
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is None and username:
            username_normalizado = formatear_rut(username)
            if username_normalizado and username_normalizado != username:
                user = authenticate(request, username=username_normalizado, password=password)
        
        if user is not None:
            login(request, user)
            if request.POST.get('remember_me'):
                request.session.set_expiry(settings.SESSION_COOKIE_AGE)
            else:
                request.session.set_expiry(0)
            return redirect(redireccion_por_rol(user))
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')

    return render(request, 'administrador/login.html')


def registro_view(request):
    """Registro público de nuevos apoderados."""
    if request.user.is_authenticated:
        return redirect(redireccion_por_rol(request.user))

    if request.method == 'POST':
        form = RegistroApoderadoForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, 'Cuenta creada correctamente. ¡Bienvenido!')
            return redirect('apoderado:dashboard')
        messages.error(request, 'Revisa los datos ingresados.')
    else:
        form = RegistroApoderadoForm()

    return render(request, 'administrador/registro.html', {'form': form})

@login_required
def dashboard_view(request):
    """Panel general de administración con datos reales de la base de datos."""
    
    total_parvulos = 0 

    asistencia_hoy = 0

    docentes_activos = 0

    alertas_activas = 0

    context = {
        'total_parvulos': total_parvulos,
        'asistencia_hoy': asistencia_hoy,
        'docentes_activos': docentes_activos,
        'alertas_activas': alertas_activas,
    }
    return render(request, 'administrador/dashboard.html', context)


@rol_requerido(Usuario.Roles.ADMINISTRADOR)
def usuarios_lista_view(request):
    """Listado y búsqueda de apoderados, docentes y recepción."""
    busqueda = request.GET.get('q', '').strip()
    rol_seleccionado = request.GET.get('rol', '')
    estado = request.GET.get('estado', '')

    usuarios = Usuario.objects.filter(
        rol__in=ROLES_GESTIONADOS,
        is_superuser=False,
    ).order_by('rol', 'first_name', 'last_name')

    if busqueda:
        usuarios = usuarios.filter(
            Q(first_name__icontains=busqueda)
            | Q(last_name__icontains=busqueda)
            | Q(rut__icontains=busqueda)
            | Q(email__icontains=busqueda)
            | Q(username__icontains=busqueda)
        )

    if rol_seleccionado in ROLES_GESTIONADOS:
        usuarios = usuarios.filter(rol=rol_seleccionado)

    if estado == 'activos':
        usuarios = usuarios.filter(is_active=True)
    elif estado == 'inactivos':
        usuarios = usuarios.filter(is_active=False)

    context = {
        'usuarios': usuarios,
        'roles_disponibles': [
            (valor, etiqueta)
            for valor, etiqueta in Usuario.Roles.choices
            if valor in ROLES_GESTIONADOS
        ],
        'busqueda': busqueda,
        'rol_seleccionado': rol_seleccionado,
        'estado_seleccionado': estado,
        'total_usuarios': usuarios.count(),
    }
    return render(request, 'administrador/usuarios_lista.html', context)


@rol_requerido(Usuario.Roles.ADMINISTRADOR)
def usuario_crear_view(request):
    """Crea una cuenta de apoderado, docente o recepción."""
    if request.method == 'POST':
        form = UsuarioAdminCreateForm(request.POST)
        if form.is_valid():
            usuario = form.save()
            messages.success(
                request,
                f'Usuario {usuario.get_full_name()} creado correctamente.',
            )
            return redirect('administrador:usuarios')
        messages.error(request, 'Revisa los datos ingresados.')
    else:
        form = UsuarioAdminCreateForm()

    return render(
        request,
        'administrador/usuario_form.html',
        {'form': form, 'modo': 'crear'},
    )


@rol_requerido(Usuario.Roles.ADMINISTRADOR)
def usuario_editar_view(request, user_id):
    """Edita datos, rol y opcionalmente la contraseña de un usuario."""
    usuario = get_object_or_404(
        Usuario,
        pk=user_id,
        rol__in=ROLES_GESTIONADOS,
        is_superuser=False,
    )

    if request.method == 'POST':
        form = UsuarioAdminUpdateForm(request.POST, instance=usuario)
        if form.is_valid():
            usuario = form.save()
            messages.success(
                request,
                f'Usuario {usuario.get_full_name()} actualizado correctamente.',
            )
            return redirect('administrador:usuarios')
        messages.error(request, 'Revisa los datos ingresados.')
    else:
        form = UsuarioAdminUpdateForm(instance=usuario)

    return render(
        request,
        'administrador/usuario_form.html',
        {'form': form, 'modo': 'editar', 'usuario': usuario},
    )


@rol_requerido(Usuario.Roles.ADMINISTRADOR)
@require_POST
def usuario_desactivar_view(request, user_id):
    """Desactiva una cuenta conservando todo su historial."""
    usuario = get_object_or_404(
        Usuario,
        pk=user_id,
        rol__in=ROLES_GESTIONADOS,
        is_superuser=False,
    )
    if usuario == request.user:
        messages.error(request, 'No puedes desactivar tu propia cuenta.')
    elif not usuario.is_active:
        messages.info(request, 'La cuenta ya estaba desactivada.')
    else:
        usuario.is_active = False
        usuario.save(update_fields=['is_active'])
        messages.success(
            request,
            f'Usuario {usuario.get_full_name()} desactivado. Su historial se conserva.',
        )
    return redirect('administrador:usuarios')


@rol_requerido(Usuario.Roles.ADMINISTRADOR)
@require_POST
def usuario_activar_view(request, user_id):
    """Reactiva una cuenta previamente desactivada."""
    usuario = get_object_or_404(
        Usuario,
        pk=user_id,
        rol__in=ROLES_GESTIONADOS,
        is_superuser=False,
    )
    if usuario.is_active:
        messages.info(request, 'La cuenta ya estaba activa.')
    else:
        usuario.is_active = True
        usuario.save(update_fields=['is_active'])
        messages.success(
            request,
            f'Usuario {usuario.get_full_name()} reactivado correctamente.',
        )
    return redirect('administrador:usuarios')


def logout_view(request):
    """Cierra la sesión del usuario y lo redirige al login."""
    logout(request)
    return redirect('administrador:login')