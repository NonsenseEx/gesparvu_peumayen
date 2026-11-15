"""
Formularios de gestión de Usuarios con validación de RUT chileno.
"""
import re

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Usuario
from .validators import validar_rut_chileno, formatear_rut
from apoderado.models import Apoderado


def validar_password_estricta(password):
    """Valida la política de contraseña fuerte usada en los registros."""
    errores = []
    if len(password) < 8:
        errores.append("al menos 8 caracteres")
    if not re.search(r'[a-z]', password):
        errores.append("una minúscula")
    if not re.search(r'[A-Z]', password):
        errores.append("una mayúscula")
    if not re.search(r'\d', password):
        errores.append("un número")
    if not re.search(r'[^A-Za-z0-9]', password):
        errores.append("un símbolo")
    if errores:
        raise ValidationError(
            "La contraseña debe incluir " + ", ".join(errores) + "."
        )


class UsuarioBaseForm(forms.ModelForm):
    """Base con validaciones comunes para crear/editar usuarios."""

    class Meta:
        model = Usuario
        fields = ['rut', 'first_name', 'last_name', 'email', 'telefono', 'rol']
        widgets = {
            'rut': forms.TextInput(attrs={'placeholder': '12345678-9', 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'placeholder': '+56912345678', 'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        rut = cleaned_data.get('rut')
        if rut:
            from .validators import formatear_rut
            cleaned_data['rut'] = formatear_rut(rut)
        return cleaned_data

    def clean_rut(self):
        rut = formatear_rut(self.cleaned_data.get('rut', ''))
        validar_rut_chileno(rut)
        return rut

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono', '')
        if not telefono:
            return telefono
        # Normaliza a +56XXXXXXXXX
        limpio = ''.join(c for c in telefono if c.isdigit() or c == '+')
        if limpio.startswith('+56'):
            normalizado = limpio
        elif limpio.startswith('56'):
            normalizado = '+' + limpio
        elif limpio.startswith('9') and len(limpio) == 9:
            normalizado = '+56' + limpio
        else:
            raise forms.ValidationError("Formato de teléfono inválido. Ejemplo: +56912345678")
        if len(normalizado) != 12:
            raise forms.ValidationError("El teléfono debe tener 9 dígitos (formato +569XXXXXXXX).")
        return normalizado


class UsuarioCreateForm(UsuarioBaseForm, UserCreationForm):
    """Creación de Usuario con contraseña."""
    password1 = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Mínimo 8 caracteres, no solo numérica."
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta(UsuarioBaseForm.Meta):
        fields = ['rut', 'first_name', 'last_name', 'email', 'telefono', 'rol']

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return p2


class UsuarioUpdateForm(UsuarioBaseForm):
    """Edición de Usuario (sin contraseña)."""
    pass


class RegistroApoderadoForm(UsuarioBaseForm, UserCreationForm):
    """Registro público de apoderados con creación de su perfil asociado."""

    class Meta(UsuarioBaseForm.Meta):
        fields = ['rut', 'first_name', 'last_name', 'email', 'telefono']
        labels = {
            'rut': 'RUN',
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
            'email': 'Correo electrónico',
            'telefono': 'Teléfono',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.fields['telefono'].required = True
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar contraseña'

    def clean_rut(self):
        rut = super().clean_rut()
        if Apoderado.objects.filter(rut=rut).exists():
            raise ValidationError("Ya existe un apoderado registrado con este RUT.")
        if Usuario.objects.filter(username=rut).exists():
            raise ValidationError("Ya existe una cuenta registrada con este RUT.")
        return rut

    def clean_password1(self):
        password = self.cleaned_data.get('password1') or ''
        if password:
            validar_password_estricta(password)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.rut
        user.rol = Usuario.Roles.APODERADO
        if commit:
            with transaction.atomic():
                user.save()
                Apoderado.objects.create(
                    usuario=user,
                    rut=user.rut,
                    nombres=user.first_name,
                    apellidos=user.last_name,
                    telefono_contacto=user.telefono or '',
                    es_titular=True,
                )
        return user


class UsuarioAdminCreateForm(UsuarioBaseForm, UserCreationForm):
    """Alta de usuarios desde el panel administrador."""

    ROLES_GESTIONADOS = [
        Usuario.Roles.DOCENTE,
        Usuario.Roles.APODERADO,
        Usuario.Roles.RECEPCION,
    ]

    class Meta(UsuarioBaseForm.Meta):
        fields = ['rut', 'first_name', 'last_name', 'email', 'telefono', 'rol']
        labels = {
            'rut': 'RUN',
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
            'email': 'Correo electrónico',
            'telefono': 'Teléfono',
            'rol': 'Rol',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rol'].choices = [
            (valor, etiqueta)
            for valor, etiqueta in Usuario.Roles.choices
            if valor in self.ROLES_GESTIONADOS
        ]
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})
        self.fields['password1'].label = 'Contraseña'
        self.fields['password2'].label = 'Confirmar contraseña'
        self.fields['password1'].help_text = (
            'Mínimo 8 caracteres e incluir mayúscula, minúscula, número y símbolo.'
        )

    def clean_rut(self):
        rut = super().clean_rut()
        if Apoderado.objects.filter(rut=rut).exists():
            raise ValidationError("Ya existe un apoderado registrado con este RUT.")
        if Usuario.objects.filter(username=rut).exists():
            raise ValidationError("Ya existe una cuenta registrada con este RUT.")
        return rut

    def clean_password1(self):
        password = self.cleaned_data.get('password1') or ''
        if password:
            validar_password_estricta(password)
        return password

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.rut
        if commit:
            with transaction.atomic():
                user.save()
                if user.rol == Usuario.Roles.APODERADO:
                    Apoderado.objects.create(
                        usuario=user,
                        rut=user.rut,
                        nombres=user.first_name,
                        apellidos=user.last_name,
                        telefono_contacto=user.telefono or '',
                        es_titular=True,
                    )
        return user


class UsuarioAdminUpdateForm(UsuarioBaseForm):
    """Edición de usuarios desde el panel administrador."""

    ROLES_GESTIONADOS = UsuarioAdminCreateForm.ROLES_GESTIONADOS

    password1 = forms.CharField(
        label="Nueva contraseña",
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
        help_text="Déjala en blanco para conservar la contraseña actual.",
    )
    password2 = forms.CharField(
        label="Confirmar nueva contraseña",
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control'}),
    )

    class Meta(UsuarioBaseForm.Meta):
        fields = ['rut', 'first_name', 'last_name', 'email', 'telefono', 'rol']
        labels = {
            'rut': 'RUN',
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
            'email': 'Correo electrónico',
            'telefono': 'Teléfono',
            'rol': 'Rol',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rol'].choices = [
            (valor, etiqueta)
            for valor, etiqueta in Usuario.Roles.choices
            if valor in self.ROLES_GESTIONADOS
        ]
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True

    def clean_rut(self):
        rut = super().clean_rut()
        perfil_rut = Apoderado.objects.filter(rut=rut).exclude(usuario=self.instance)
        if perfil_rut.exists():
            raise ValidationError("Ya existe un apoderado registrado con este RUT.")
        cuentas = Usuario.objects.filter(username=rut).exclude(pk=self.instance.pk)
        if cuentas.exists():
            raise ValidationError("Ya existe una cuenta registrada con este RUT.")
        return rut

    def clean(self):
        cleaned_data = super().clean()
        nuevo_rol = cleaned_data.get('rol')
        if (
            self.instance.pk
            and self.instance.rol == Usuario.Roles.APODERADO
            and nuevo_rol != Usuario.Roles.APODERADO
        ):
            perfil = getattr(self.instance, 'perfil_apoderado', None)
            if perfil and (
                perfil.hijos_a_cargo.exists()
                or perfil.retiros_efectuados.exists()
                or perfil.parvulos_autorizados.exists()
            ):
                raise ValidationError(
                    "No se puede cambiar el rol: el apoderado tiene párvulos o "
                    "retiros asociados. Desactiva la cuenta si ya no debe usarse."
                )
        return cleaned_data

    def clean_password1(self):
        password = self.cleaned_data.get('password1') or ''
        if password:
            validar_password_estricta(password)
        return password

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 or p2:
            if not p1:
                raise ValidationError("Ingresa la nueva contraseña o deja ambos campos vacíos.")
            if p1 != p2:
                raise ValidationError("Las contraseñas no coinciden.")
        return p2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.rut
        password = self.cleaned_data.get('password1')
        if password:
            user.set_password(password)
        if commit:
            with transaction.atomic():
                user.save()
                if user.rol == Usuario.Roles.APODERADO:
                    perfil = getattr(user, 'perfil_apoderado', None)
                    if perfil is None:
                        perfil = Apoderado(usuario=user)
                    perfil.rut = user.rut
                    perfil.nombres = user.first_name
                    perfil.apellidos = user.last_name
                    perfil.telefono_contacto = user.telefono or ''
                    perfil.es_titular = True
                    perfil.save()
                else:
                    perfil = getattr(user, 'perfil_apoderado', None)
                    if perfil:
                        perfil.delete()
        return user
