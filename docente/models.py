from django.db import models
from django.conf import settings
from django.utils import timezone

class Parvulo(models.Model):
    class Niveles(models.TextChoices):
        SALA_CUNA = 'SALA_CUNA', 'Sala Cuna'
        NIVEL_MEDIO = 'NIVEL_MEDIO', 'Nivel Medio'
        TRANSICION = 'TRANSICION', 'Transición'

    class Estados(models.TextChoices):
        AUSENTE = 'AUSENTE', 'Ausente'
        PRESENTE = 'PRESENTE', 'Presente en Aula'
        EN_VERIFICACION = 'EN_VERIFICACION', 'En Proceso de Retiro'
        RETIRADO = 'RETIRADO', 'Retirado del Establecimiento'

    rut = models.CharField(max_length=12, unique=True)
    nombre = models.CharField(max_length=80)
    apellido = models.CharField(max_length=80)
    fecha_nacimiento = models.DateField()
    sala_nivel = models.CharField(max_length=20, choices=Niveles.choices)
    estado_actual = models.CharField(max_length=20, choices=Estados.choices, default=Estados.AUSENTE)
    detalles_medicos = models.TextField(blank=True, help_text="Alergias o condiciones de salud")

    # Relación con el apoderado legal
    apoderado_titular = models.ForeignKey(
        'apoderado.Apoderado', 
        on_delete=models.PROTECT, 
        related_name='hijos_a_cargo'
    )
    # Límite normativo de hasta 3 terceros autorizados
    terceros_autorizados = models.ManyToManyField(
        'apoderado.Apoderado', 
        blank=True, 
        related_name='parvulos_autorizados'
    )

    class Meta:
        verbose_name = "Párvulo"
        verbose_name_plural = "Párvulos"

    def __str__(self):
        return f"{self.nombre} {self.apellido} ({self.sala_nivel})"


class Asistencia(models.Model):
    class EstadosAsistencia(models.TextChoices):
        PRESENTE = 'PRESENTE', 'Presente'
        AUSENTE = 'AUSENTE', 'Ausente'
        JUSTIFICADO = 'JUSTIFICADO', 'Inasistencia Justificada' 

    parvulo = models.ForeignKey(Parvulo, on_delete=models.CASCADE, related_name='asistencias')
    fecha = models.DateField(default=timezone.localdate)
    hora_ingreso = models.TimeField(null=True, blank=True)
    estado = models.CharField(max_length=15, choices=EstadosAsistencia.choices, default=EstadosAsistencia.AUSENTE)
    justificacion = models.TextField(blank=True, null=True)
    docente_responsable = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.PROTECT, 
        null=True, 
        blank=True
    )

    class Meta:
        unique_together = ('parvulo', 'fecha')
        verbose_name = "Registro de Asistencia"
        verbose_name_plural = "Registros de Asistencia"

    def __str__(self):
        return f"{self.parvulo.nombre} - {self.fecha} ({self.estado})"