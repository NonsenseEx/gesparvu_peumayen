"""
Validadores reutilizables del Proyecto Guarderia  (GESPARVU).
"""
from django.core.exceptions import ValidationError
import re


def formatear_rut(rut: str) -> str:
    """Normaliza un RUT a formato 12345678-9 (sin puntos, con guion)."""
    limpio = re.sub(r"[^0-9kK]", "", rut or "").upper()
    if len(limpio) < 2:
        return limpio
    return f"{limpio[:-1]}-{limpio[-1]}"


def calcular_dv(cuerpo: str) -> str:
    """Calcula el Dígito Verificador (módulo 11) del cuerpo del RUT."""
    suma, multiplo = 0, 2
    for c in reversed(cuerpo):
        suma += int(c) * multiplo
        multiplo = 2 if multiplo == 7 else multiplo + 1
    resto = 11 - (suma % 11)
    if resto == 11:
        return "0"
    if resto == 10:
        return "K"
    return str(resto)


def validar_rut_chileno(value: str) -> None:
    """
    Valida un RUT chileno completo (cuerpo + DV) con módulo 11.
    Acepta con o sin puntos y guion. Lanza ValidationError si no es válido.
    """
    rut_normalizado = formatear_rut(value)
    if "-" not in rut_normalizado:
        raise ValidationError("El RUT debe incluir cuerpo y dígito verificador.")

    cuerpo, dv = rut_normalizado.split("-")
    if not cuerpo.isdigit() or len(cuerpo) < 7 or len(cuerpo) > 8:
        raise ValidationError("El cuerpo del RUT debe tener entre 7 y 8 dígitos.")

    if calcular_dv(cuerpo) != dv:
        raise ValidationError("El dígito verificador del RUT no es válido.")


MAX_IMAGEN_MB = 5
FORMATOS_IMAGEN_PERMITIDOS = {'image/jpeg', 'image/png', 'image/webp'}


def validar_imagen_perfil(imagen) -> None:
    """Valida tamaño y formato de una imagen de perfil (JPG, PNG o WEBP)."""
    if not imagen:
        return
    limite = MAX_IMAGEN_MB * 1024 * 1024
    if imagen.size > limite:
        raise ValidationError(f"La imagen no puede superar los {MAX_IMAGEN_MB} MB.")
    formato = (getattr(imagen, 'content_type', '') or '').lower()
    if formato and formato not in FORMATOS_IMAGEN_PERMITIDOS:
        raise ValidationError("Formato no permitido. Usa una imagen JPG, PNG o WEBP.")
