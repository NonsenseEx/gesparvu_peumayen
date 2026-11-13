from django.contrib import admin

from .models import Mensaje


@admin.register(Mensaje)
class MensajeAdmin(admin.ModelAdmin):
    list_display = ('fecha_hora', 'autor', 'sala', 'contenido')
    list_filter = ('sala', 'autor')
    search_fields = ('contenido', 'autor__username', 'autor__first_name', 'autor__last_name')
