import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import Mensaje

ROLES_PERMITIDOS = {'ADMIN', 'DOCENTE', 'RECEPCION'}
SALA_CHAT = 'docente'


class ChatConsumer(AsyncWebsocketConsumer):
    """Chat compartido entre administración, recepción y docentes."""

    async def connect(self):
        user = self.scope.get('user')
        if not user or not user.is_authenticated or user.rol not in ROLES_PERMITIDOS:
            await self.close()
            return

        self.grupo = f'chat_{SALA_CHAT}'
        await self.channel_layer.group_add(self.grupo, self.channel_name)
        await self.accept()

        historial = await self.obtener_historial()
        for mensaje in historial:
            await self.send(text_data=json.dumps(mensaje))

    async def disconnect(self, close_code):
        if hasattr(self, 'grupo'):
            await self.channel_layer.group_discard(self.grupo, self.channel_name)

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
        except (TypeError, ValueError):
            return

        contenido = (data.get('mensaje') or '').strip()
        if not contenido:
            return
        contenido = contenido[:1000]

        mensaje = await self.guardar_mensaje(contenido)
        await self.channel_layer.group_send(
            self.grupo,
            {'type': 'chat_message', 'mensaje': mensaje},
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps(event['mensaje']))

    @database_sync_to_async
    def guardar_mensaje(self, contenido):
        user = self.scope['user']
        mensaje = Mensaje.objects.create(
            autor=user,
            sala=SALA_CHAT,
            contenido=contenido,
        )
        return self.serializar(mensaje)

    @database_sync_to_async
    def obtener_historial(self):
        mensajes = Mensaje.objects.filter(sala=SALA_CHAT).select_related('autor')[:50]
        return [self.serializar(m) for m in mensajes]

    def serializar(self, mensaje):
        autor = mensaje.autor
        return {
            'id': mensaje.id,
            'autor': autor.get_full_name() or autor.username,
            'rol': 'Administrador' if autor.is_superuser else autor.get_rol_display(),
            'contenido': mensaje.contenido,
            'fecha_hora': mensaje.fecha_hora.strftime('%H:%M'),
            'propio': autor.id == self.scope['user'].id,
        }
