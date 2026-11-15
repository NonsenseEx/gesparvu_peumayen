from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from .models import Apoderado
from .services import regenerar_token_qr, generar_imagen_qr_base64
# Importa tus modelos reales aquí:
# from .models import Parvulo, Novedad


def _obtener_apoderado(user):
    """Devuelve el perfil de apoderado asociado al usuario autenticado."""
    return Apoderado.objects.filter(usuario=user).first()


@login_required
def dashboard_view(request):
    """Vista principal del apoderado con acceso a la generación de su QR."""
    apoderado = _obtener_apoderado(request.user)
    parvulos = []
    if apoderado is not None:
        parvulos = list(apoderado.hijos_a_cargo.all()) + list(apoderado.parvulos_autorizados.all())

    context = {
        'apoderado': apoderado,
        'parvulos': parvulos,
        'qr_vigente': bool(apoderado and apoderado.token_qr_actual and apoderado.token_qr_expira and apoderado.token_qr_expira > timezone.now()),
    }
    return render(request, 'apoderado/dashboard.html', context)


@login_required
def generar_qr_view(request):
    """Genera (o regenera) el código QR del apoderado y lo muestra en pantalla."""
    apoderado = _obtener_apoderado(request.user)
    if apoderado is None:
        messages.error(request, 'Tu usuario no tiene un perfil de apoderado asociado.')
        return redirect('apoderado:dashboard')

    token = regenerar_token_qr(apoderado)
    qr_base64 = generar_imagen_qr_base64(token)

    context = {
        'apoderado': apoderado,
        'qr_base64': qr_base64,
        'token': token,
        'expira': apoderado.token_qr_expira,
    }
    return render(request, 'apoderado/generar_qr.html', context)


@login_required
def ficha_parvulo_view(request, parvulo_id):
    """Detalle técnico y médico del párvulo."""
    # parvulo = get_object_or_404(Parvulo, pk=parvulo_id, apoderado=request.user)

    context = {
        # 'parvulo': parvulo,
    }
    return render(request, 'apoderado/ficha_parvulo.html', context)
