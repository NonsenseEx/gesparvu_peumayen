from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# Importa tus modelos reales aquí:
# from .models import Parvulo, Novedad

@login_required
def dashboard_view(request):
    """Vista del docente con la lista de párvulos a su cargo y control de la sala."""
    # Consultas a la Base de Datos:
    # parvulos_sala = Parvulo.objects.filter(sala__educadora=request.user)

    context = {
        # 'parvulos_sala': parvulos_sala,
    }
    return render(request, 'docente/dashboard.html', context)

@login_required
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

    # Para cargar el <select> de párvulos en el formulario:
    # parvulos = Parvulo.objects.filter(sala__educadora=request.user)
    
    context = {
        # 'parvulos': parvulos,
    }
    return render(request, 'docente/registrar_actividad.html', context)
