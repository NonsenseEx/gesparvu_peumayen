from django.conf import settings
from django.db import models


class Mensaje(models.Model):
    """Mensaje del chat compartido entre administración, recepción y docentes."""

    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mensajes_chat'
    )
    sala = models.CharField(max_length=50, default='docente')
    contenido = models.TextField()
    fecha_hora = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['fecha_hora']
        verbose_name = "Mensaje de Chat"
        verbose_name_plural = "Mensajes de Chat"

    def __str__(self):
        return f"{self.autor}: {self.contenido[:50]}"
