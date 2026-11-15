from django.urls import path

from .consumers import ChatConsumer

websocket_urlpatterns = [
    path('ws/chat/docente/', ChatConsumer.as_asgi()),
]
