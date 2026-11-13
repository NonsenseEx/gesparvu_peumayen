from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    class Roles(models.TextChoices):
        ADMINISTRADOR = 'ADMIN', 'Administrador'
        DOCENTE = 'DOCENTE', 'Docente / Educadora'
        RECEPCION = 'RECEPCION', 'Personal de Recepción'
        APODERADO = 'APODERADO', 'Apoderado / Autorizado'

    rut = models.CharField(max_length=12, unique=True, verbose_name="RUN")
    telefono = models.CharField(max_length=15, blank=True, null=True)
    rol = models.CharField(max_length=15, choices=Roles.choices, default=Roles.RECEPCION)

    def __str__(self):
        return f"{self.get_full_name()} ({self.get_rol_display()}) - {self.rut}"


class EmergenciaPISE(models.Model):
    class TiposEmergencia(models.TextChoices):
        SISMO = 'SISMO', 'Sismo / Terremoto'
        INCENDIO = 'INCENDIO', 'Incendio'
        FUGA_GAS = 'FUGA_GAS', 'Fuga de Gas'
        SIMULACRO = 'SIMULACRO', 'Simulacro Programado'

    activado_por = models.ForeignKey(Usuario, on_delete=models.PROTECT, related_name='emergencias_activadas')
    tipo_emergencia = models.CharField(max_length=20, choices=TiposEmergencia.choices)
    fecha_hora_inicio = models.DateTimeField(auto_now_add=True)
    aforo_al_evacuar = models.PositiveSmallIntegerField(help_text="Párvulos presentes en sala")
    finalizada = models.BooleanField(default=False)
    observaciones = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = "Emergencia PISE"
        verbose_name_plural = "Emergencias PISE"

    def __str__(self):
        return f"Alerta {self.tipo_emergencia} - {self.fecha_hora_inicio.strftime('%d/%m/%Y %H:%M')}"