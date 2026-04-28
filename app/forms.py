from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import Usuario, Asignacion, EntregaAsignacion
from django.core.exceptions import ValidationError
import re


class RegistroForm(UserCreationForm):
    CODIGO_PROFESOR = 'PrfsrJapon1077'

    telefono = forms.CharField(
        max_length=10,
        widget=forms.TextInput(attrs={
            'placeholder': 'Ej: 0991234567',
            'pattern': '[0-9]{10}',
            'maxlength': '10',
            'title': 'Ingrese exactamente 10 números',
        })
    )

    tipo_usuario = forms.ChoiceField(
        choices=Usuario.ROLES,
        initial='estudiante'
    )

    codigo_verificacion_profesor = forms.CharField(
        required=False,
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Código exclusivo para profesores'
        })
    )

    pregunta_seguridad = forms.ChoiceField(
        choices=Usuario.PREGUNTAS
    )

    class Meta:
        model = Usuario
        fields = [
            'username',
            'email',
            'telefono',
            'tipo_usuario',
            'password1',
            'password2',
            'pregunta_seguridad',
            'respuesta_seguridad'
        ]

    def clean_telefono(self):
        telefono = self.cleaned_data.get('telefono')

        if not re.fullmatch(r'\d{10}', telefono):
            raise ValidationError("El teléfono debe tener exactamente 10 números.")

        return telefono

    def clean(self):
        cleaned_data = super().clean()
        tipo_usuario = cleaned_data.get('tipo_usuario')
        codigo = cleaned_data.get('codigo_verificacion_profesor')

        if tipo_usuario == 'profesor' and codigo != self.CODIGO_PROFESOR:
            self.add_error(
                'codigo_verificacion_profesor',
                'Código de verificación de profesor inválido.'
            )

        return cleaned_data


# =========================
# 📚 FORMS PARA ASIGNACIONES
# =========================

class AsignacionForm(forms.ModelForm):
    """Formulario para crear/editar asignaciones"""
    class Meta:
        model = Asignacion
        fields = ['titulo', 'descripcion', 'fecha_limite']
        widgets = {
            'titulo': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Título de la asignación'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Descripción detallada de la tarea'}),
            'fecha_limite': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }


class EntregaAsignacionForm(forms.ModelForm):
    """Formulario para que los estudiantes suban sus entregas"""
    class Meta:
        model = EntregaAsignacion
        fields = ['archivo', 'comentario_estudiante']
        widgets = {
            'archivo': forms.FileInput(attrs={'class': 'form-control'}),
            'comentario_estudiante': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Comentarios adicionales (opcional)'}),
        }


class CalificacionForm(forms.ModelForm):
    """Formulario para que los profesores califiquen las entregas"""
    class Meta:
        model = EntregaAsignacion
        fields = ['calificacion', 'comentario_profesor']
        widgets = {
            'calificacion': forms.NumberInput(attrs={'class': 'form-control', 'min': '0', 'max': '100', 'step': '0.01'}),
            'comentario_profesor': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Comentarios y retroalimentación para el estudiante'}),
        }
