from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from administrador.mixins import rol_requerido
from administrador.models import Usuario
from .models import Parvulo

@rol_requerido(Usuario.Roles.DOCENTE, Usuario.Roles.ADMINISTRADOR)
def dashboard_view(request):
    """Vista del docente con la lista de párvulos de su nivel y control de la sala."""
    if request.user.is_superuser or request.user.rol == Usuario.Roles.ADMINISTRADOR:
        parvulos_sala = Parvulo.objects.all()
    elif request.user.sala_nivel:
        parvulos_sala = Parvulo.objects.filter(sala_nivel=request.user.sala_nivel)
    else:
        parvulos_sala = Parvulo.objects.none()

    parvulos_sala = parvulos_sala.select_related('apoderado_titular').order_by(
        'apellido', 'nombre'
    )

    context = {
        'parvulos_sala': parvulos_sala,
        'nivel_asignado': request.user.sala_nivel,
    }
    return render(request, 'docente/dashboard.html', context)


@rol_requerido(Usuario.Roles.DOCENTE, Usuario.Roles.ADMINISTRADOR)
def ficha_parvulo_view(request, parvulo_id):
    """Ficha de datos personales, salud y contacto de emergencia del párvulo."""
    parvulo = get_object_or_404(
        Parvulo.objects.select_related('apoderado_titular').prefetch_related(
            'terceros_autorizados'
        ),
        pk=parvulo_id,
    )

    if (
        not request.user.is_superuser
        and request.user.rol == Usuario.Roles.DOCENTE
        and parvulo.sala_nivel != request.user.sala_nivel
    ):
        raise PermissionDenied(
            'No tienes permiso para acceder a párvulos de otro nivel.'
        )

    context = {
        'parvulo': parvulo,
        'titular': parvulo.apoderado_titular,
        'terceros': parvulo.terceros_autorizados.all(),
        'puede_editar': (
            request.user.is_superuser
            or request.user.rol == Usuario.Roles.ADMINISTRADOR
        ),
    }
    return render(request, 'parvulos/ficha_parvulo.html', context)


@rol_requerido(Usuario.Roles.DOCENTE, Usuario.Roles.ADMINISTRADOR)
def registrar_actividad_view(request):
    """Formulario para guardar observaciones, alimentación o eventos pedagógicos."""
    if request.method == 'POST':
        parvulo_id = request.POST.get('parvulo')
        categoria = request.POST.get('categoria')
        observaciones = request.POST.get('observaciones')

        # Guardar en Base de Datos:
        # Novedad.objects.create(
        #     parvulo_id=parvulo_id,
        #     categoria=categoria,
        #     observacion=observaciones,
        #     registrado_por=request.user
        # )
        messages.success(request, 'Actividad registrada correctamente.')
        return redirect('docente:dashboard')

    if request.user.is_superuser or request.user.rol == Usuario.Roles.ADMINISTRADOR:
        parvulos = Parvulo.objects.all()
    elif request.user.sala_nivel:
        parvulos = Parvulo.objects.filter(sala_nivel=request.user.sala_nivel)
    else:
        parvulos = Parvulo.objects.none()

    context = {
        'parvulos': parvulos.order_by('apellido', 'nombre'),
    }
    return render(request, 'docente/registrar_actividad.html', context)
