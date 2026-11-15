import secrets
import qrcode
import io
import base64
from django.utils import timezone
from datetime import timedelta

def regenerar_token_qr(apoderado):
    """
    Genera un nuevo token único para el apoderado y establece su expiración.
    """
    # Genera un token seguro de 32 bytes
    nuevo_token = secrets.token_urlsafe(32)
    apoderado.token_qr_actual = nuevo_token
    # Expira en 10 minutos (puedes ajustar este tiempo)
    apoderado.token_qr_expira = timezone.now() + timedelta(minutes=10)
    apoderado.save(update_fields=['token_qr_actual', 'token_qr_expira'])
    return nuevo_token

def generar_imagen_qr_base64(token):
    """
    Genera la imagen del QR en base64 para mostrarla en el template.
    """
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode()