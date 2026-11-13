import json

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.http import require_POST
from apoderado.models import Apoderado
# Importa tus modelos reales aquí:
# from .models import Parvulo, Asistencia


@login_required
def dashboard_view(request):
    """Panel general de portería y recepción."""
    # Consultas a la Base de Datos:
    # ultimos_movimientos = Asistencia.objects.filter(fecha=timezone.now().date()).order_by('-hora')[:10]

    context = {
        # 'ultimos_movimientos': ultimos_movimientos,
    }
    return render(request, 'recepcion/dashboard.html', context)


@login_required
def registro_asistencia_view(request):
    """Formulario específico para marcar entradas y salidas escaneando/digitando el RUT."""
    if request.method == 'POST':
        rut_ingresado = request.POST.get('rut')

        # Buscar en la Base de Datos y registrar marcaje:
        # parvulo = Parvulo.objects.filter(rut=rut_ingresado).first()
        # if parvulo:
        #     Asistencia.objects.create(
        #         parvulo=parvulo,
        #         tipo='ENTRADA', # o cambiar según lógica de salida
        #         fecha_hora=timezone.now()
        #     )
        #     messages.success(request, f'Asistencia registrada para {parvulo.nombre}')
        # else:
        #     messages.error(request, 'Párvulo o RUT no encontrado.')

        return redirect('recepcion:registro_asistencia')

    # Listado general de asistencia de la jornada:
    # asistencias_hoy = Asistencia.objects.filter(fecha=timezone.now().date())

    context = {
        # 'asistencias_hoy': asistencias_hoy,
    }
    return render(request, 'recepcion/registro_asistencia.html', context)


@login_required
@require_POST
def validar_qr_view(request):
    """Valida el token de un QR escaneado y devuelve el apoderado y sus párvulos."""
    token = None
    if request.content_type == 'application/json':
        try:
            token = json.loads(request.body).get('token')
        except (TypeError, ValueError):
            token = None
    else:
        token = request.POST.get('token')

    token = (token or '').strip()
    if not token:
        return JsonResponse(
            {'valido': False, 'error': 'No se recibió ningún código QR.'},
            status=400,
        )

    apoderado = Apoderado.objects.filter(token_qr_actual=token).first()
    if apoderado is None:
        return JsonResponse(
            {'valido': False, 'error': 'El código QR no corresponde a un apoderado registrado.'},
            status=404,
        )

    if not apoderado.token_qr_expira or apoderado.token_qr_expira < timezone.now():
        return JsonResponse(
            {'valido': False, 'error': 'El código QR está vencido. Solicita uno nuevo al apoderado.'},
            status=410,
        )

    parvulos = list(apoderado.hijos_a_cargo.all()) + list(apoderado.parvulos_autorizados.all())
    parvulos_unicos = {p.id: p for p in parvulos}

    return JsonResponse({
        'valido': True,
        'apoderado': {
            'nombre': f'{apoderado.nombres} {apoderado.apellidos}',
            'rut': apoderado.rut,
            'tipo': 'Titular' if apoderado.es_titular else 'Tercero Autorizado',
        },
        'parvulos': [
            {
                'nombre': f'{p.nombre} {p.apellido}',
                'rut': p.rut,
                'nivel': p.get_sala_nivel_display(),
                'estado': p.get_estado_actual_display(),
            }
            for p in parvulos_unicos.values()
        ],
        'expira': apoderado.token_qr_expira.strftime('%d/%m/%Y %H:%M'),
    })
