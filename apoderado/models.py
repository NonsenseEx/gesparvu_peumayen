from django.db import models
from django.conf import settings

class Apoderado(models.Model):
    # Opcional si el apoderado tiene cuenta web en el sistema
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True,
        related_name='perfil_apoderado'
    )
    rut = models.CharField(max_length=12, unique=True, verbose_name="RUN")
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100)
    telefono_contacto = models.CharField(max_length=15)
    es_titular = models.BooleanField(default=True, help_text="False si es un tercero autorizado")
    token_qr_actual = models.CharField(max_length=255, blank=True, null=True, unique=True)
    token_qr_expira = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = "Apoderado / Autorizado"
        verbose_name_plural = "Apoderados y Autorizados"

    def __str__(self):
        tipo = "Titular" if self.es_titular else "Tercero Autorizado"
        return f"{self.nombres} {self.apellidos} ({self.rut}) - {tipo}"