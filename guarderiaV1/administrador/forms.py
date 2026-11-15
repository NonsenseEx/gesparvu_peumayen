"""
Formularios de gestión de Usuarios con validación de RUT chileno.
"""
import re

from django import forms
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm
from django.core.exceptions import ValidationError
from django.db import transaction
from .models import Usuario
from .validators import validar_rut_chileno, formatear_rut, validar_imagen_perfil
from apoderado.models import Apoderado
from docente.models import Parvulo


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
        fields = ['rut', 'first_name', 'last_name', 'email', 'telefono', 'rol', 'sala_nivel']
        widgets = {
            'rut': forms.TextInput(attrs={'placeholder': '12345678-9', 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'telefono': forms.TextInput(attrs={'placeholder': '+56912345678', 'class': 'form-control'}),
            'rol': forms.Select(attrs={'class': 'form-select'}),
            'sala_nivel': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        rut = cleaned_data.get('rut')
        if rut:
            from .validators import formatear_rut
            cleaned_data['rut'] = formatear_rut(rut)

        rol = cleaned_data.get('rol')
        if 'sala_nivel' in self.fields:
            if rol != Usuario.Roles.DOCENTE:
                cleaned_data['sala_nivel'] = ''
            elif not cleaned_data.get('sala_nivel'):
                self.add_error(
                    'sala_nivel',
                    'Asigna un nivel/sala a los docentes para que puedan ver sus párvulos.',
                )
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

    foto = forms.ImageField(
        label="Foto de perfil",
        required=True,
        validators=[validar_imagen_perfil],
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        help_text="Obligatoria. Se usará para validar tu identidad al retirar al párvulo.",
    )

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
                    foto=self.cleaned_data.get('foto'),
                )
        return user


class UsuarioAdminCreateForm(UsuarioBaseForm, UserCreationForm):
    """Alta de usuarios desde el panel administrador."""

    ROLES_GESTIONADOS = [
        Usuario.Roles.DOCENTE,
        Usuario.Roles.APODERADO,
        Usuario.Roles.RECEPCION,
    ]

    foto_apoderado = forms.ImageField(
        label="Foto de perfil del apoderado",
        required=False,
        validators=[validar_imagen_perfil],
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        help_text="Obligatoria para apoderados: se usará para validar el retiro.",
    )

    class Meta(UsuarioBaseForm.Meta):
        fields = ['rut', 'first_name', 'last_name', 'email', 'telefono', 'rol', 'sala_nivel']
        labels = {
            'rut': 'RUN',
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
            'email': 'Correo electrónico',
            'telefono': 'Teléfono',
            'rol': 'Rol',
            'sala_nivel': 'Nivel / Sala (docentes)',
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

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('rol') == Usuario.Roles.APODERADO and not cleaned_data.get('foto_apoderado'):
            self.add_error(
                'foto_apoderado',
                'La foto de perfil es obligatoria para los apoderados.',
            )
        return cleaned_data

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
                        foto=self.cleaned_data.get('foto_apoderado'),
                    )
        return user


class UsuarioAdminUpdateForm(UsuarioBaseForm):
    """Edición de usuarios desde el panel administrador."""

    ROLES_GESTIONADOS = UsuarioAdminCreateForm.ROLES_GESTIONADOS

    foto_apoderado = forms.ImageField(
        label="Foto de perfil del apoderado",
        required=False,
        validators=[validar_imagen_perfil],
        widget=forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        help_text="Obligatoria si el apoderado aún no tiene foto registrada.",
    )

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
        fields = ['rut', 'first_name', 'last_name', 'email', 'telefono', 'rol', 'sala_nivel']
        labels = {
            'rut': 'RUN',
            'first_name': 'Nombres',
            'last_name': 'Apellidos',
            'email': 'Correo electrónico',
            'telefono': 'Teléfono',
            'rol': 'Rol',
            'sala_nivel': 'Nivel / Sala (docentes)',
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

        if nuevo_rol == Usuario.Roles.APODERADO:
            perfil = getattr(self.instance, 'perfil_apoderado', None)
            tiene_foto = bool(perfil and perfil.foto)
            if not tiene_foto and not cleaned_data.get('foto_apoderado'):
                self.add_error(
                    'foto_apoderado',
                    'La foto de perfil es obligatoria para los apoderados.',
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
                    nueva_foto = self.cleaned_data.get('foto_apoderado')
                    if nueva_foto:
                        perfil.foto = nueva_foto
                    perfil.save()
                else:
                    perfil = getattr(user, 'perfil_apoderado', None)
                    if perfil:
                        perfil.delete()
        return user

class ParvuloAdminForm(forms.ModelForm):
    """Creación y edición de la ficha de un párvulo."""

    class Meta:
        model = Parvulo
        fields = [
            'rut',
            'nombre',
            'apellido',
            'fecha_nacimiento',
            'sala_nivel',
            'estado_actual',
            'foto',
            'detalles_medicos',
            'apoderado_titular',
            'terceros_autorizados',
            'contacto_emergencia_nombre',
            'contacto_emergencia_telefono',
            'contacto_emergencia_parentesco',
        ]
        widgets = {
            'rut': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345678-9'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'sala_nivel': forms.Select(attrs={'class': 'form-select'}),
            'estado_actual': forms.Select(attrs={'class': 'form-select'}),
            'foto': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'detalles_medicos': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'apoderado_titular': forms.Select(attrs={'class': 'form-select'}),
            'terceros_autorizados': forms.SelectMultiple(attrs={'class': 'form-select', 'size': 5}),
            'contacto_emergencia_nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_emergencia_telefono': forms.TextInput(attrs={'class': 'form-control'}),
            'contacto_emergencia_parentesco': forms.TextInput(attrs={'class': 'form-control'}),
        }
        labels = {
            'rut': 'RUN',
            'nombre': 'Nombres',
            'apellido': 'Apellidos',
            'fecha_nacimiento': 'Fecha de nacimiento',
            'sala_nivel': 'Nivel / Sala',
            'estado_actual': 'Estado actual',
            'foto': 'Foto del párvulo',
            'detalles_medicos': 'Alergias / condiciones de salud',
            'apoderado_titular': 'Titular principal',
            'terceros_autorizados': 'Terceros autorizados para retiro',
            'contacto_emergencia_nombre': 'Nombre del contacto de emergencia',
            'contacto_emergencia_telefono': 'Teléfono del contacto de emergencia',
            'contacto_emergencia_parentesco': 'Parentesco del contacto de emergencia',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['apoderado_titular'].queryset = Apoderado.objects.filter(
            es_titular=True
        ).order_by('nombres', 'apellidos')
        self.fields['terceros_autorizados'].queryset = Apoderado.objects.order_by(
            'nombres', 'apellidos'
        )
        self.fields['apoderado_titular'].empty_label = 'Selecciona un titular principal'

    def clean_apoderado_titular(self):
        titular = self.cleaned_data.get('apoderado_titular')
        if titular and not titular.es_titular:
            raise ValidationError(
                'El titular principal debe estar marcado como titular en su perfil.'
            )
        return titular

    def clean(self):
        cleaned_data = super().clean()
        titular = cleaned_data.get('apoderado_titular')
        terceros = cleaned_data.get('terceros_autorizados')

        if titular and terceros and terceros.filter(pk=titular.pk).exists():
            self.add_error(
                'terceros_autorizados',
                'El titular principal no puede figurar como tercero autorizado.',
            )

        if titular:
            if not cleaned_data.get('contacto_emergencia_nombre'):
                cleaned_data['contacto_emergencia_nombre'] = (
                    f'{titular.nombres} {titular.apellidos}'.strip()
                )
            if not cleaned_data.get('contacto_emergencia_telefono'):
                cleaned_data['contacto_emergencia_telefono'] = titular.telefono_contacto

        return cleaned_data


class PasswordResetRequestForm(PasswordResetForm):
    """Solicita el enlace de recuperación usando el correo o el RUN del usuario."""

    email = forms.CharField(
        label="Correo o RUN",
        max_length=254,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'correo@ejemplo.cl o 12345678-9',
                'autocomplete': 'username',
            }
        ),
    )

    def get_users(self, identifier):
        identifier = (identifier or '').strip()
        if not identifier:
            return []
        if '@' in identifier:
            usuarios = Usuario.objects.filter(
                email__iexact=identifier, is_active=True
            ).exclude(email='')
        else:
            usuarios = Usuario.objects.filter(
                username__iexact=formatear_rut(identifier), is_active=True
            ).exclude(email='')
        return [usuario for usuario in usuarios if usuario.has_usable_password()]


class PasswordResetSetForm(SetPasswordForm):
    """Define la nueva contraseña aplicando la misma política estricta del registro."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['new_password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['new_password2'].widget.attrs.update({'class': 'form-control'})

    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1') or ''
        if password:
            validar_password_estricta(password)
        return password
