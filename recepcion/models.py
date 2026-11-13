from django.db import models
from django.conf import settings

class Retiro(models.Model):
    class Metodos(models.TextChoices):
        QR = 'QR', 'Escaneo de Código QR'
        MANUAL_RUT = 'MANUAL_RUT', 'Validación Manual por RUN'

    parvulo = models.ForeignKey('docente.Parvulo', on_delete=models.PROTECT, related_name='historial_retiros')
    retirado_por = models.ForeignKey('apoderado.Apoderado', on_delete=models.PROTECT, related_name='retiros_efectuados')
    recepcionista = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='retiros_validados')
    fecha_hora = models.DateTimeField(auto_now_add=True)
    metodo_validacion = models.CharField(max_length=15, choices=Metodos.choices, default=Metodos.QR)
    firma_digital = models.ImageField(upload_to='firmas/%Y/%m/', help_text="Captura en imagen de la firma")
    hash_firma = models.CharField(max_length=64, blank=True, null=True, help_text="SHA-256 de la firma")

    class Meta:
        verbose_name = "Registro de Retiro"
        verbose_name_plural = "Registros de Retiro"

    def __str__(self):
        return f"Retiro: {self.parvulo.nombre} por {self.retirado_por.nombres} ({self.fecha_hora.strftime('%d/%m/%Y %H:%M')})"