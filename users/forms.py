import re

from django import forms
from django.contrib.auth.forms import PasswordChangeForm, UserCreationForm
from django.core.exceptions import ValidationError

from .models import Usuario


class RegistroForm(UserCreationForm):
    CODIGO_PROFESOR = "PrfsrJapon1077"

    first_name = forms.CharField(
        label="Nombres",
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Ej: Maria Fernanda"}),
    )
    last_name = forms.CharField(
        label="Apellidos",
        max_length=150,
        widget=forms.TextInput(attrs={"placeholder": "Ej: Perez Lopez"}),
    )
    cedula = forms.CharField(
        max_length=10,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Ej: 0102030405",
                "pattern": "[0-9]{10}",
                "maxlength": "10",
                "title": "Ingrese exactamente 10 numeros",
            }
        ),
    )
    telefono = forms.CharField(
        max_length=10,
        widget=forms.TextInput(
            attrs={
                "placeholder": "Ej: 0991234567",
                "pattern": "[0-9]{10}",
                "maxlength": "10",
                "title": "Ingrese exactamente 10 numeros",
            }
        ),
    )

    tipo_usuario = forms.ChoiceField(
        choices=Usuario.ROLES,
        initial="estudiante",
    )

    codigo_verificacion_profesor = forms.CharField(
        required=False,
        widget=forms.PasswordInput(
            attrs={"placeholder": "Codigo exclusivo para profesores"}
        ),
    )
    carrera = forms.ChoiceField(
        choices=Usuario.CARRERA_CHOICES,
        widget=forms.Select(),
    )

    pregunta_seguridad = forms.ChoiceField(choices=Usuario.PREGUNTAS_SEGURIDAD)

    class Meta:
        model = Usuario
        fields = [
            "username",
            "first_name",
            "last_name",
            "cedula",
            "email",
            "carrera",
            "telefono",
            "tipo_usuario",
            "password1",
            "password2",
            "pregunta_seguridad",
            "respuesta_seguridad",
        ]

    def clean_email(self):
        email = self.cleaned_data.get("email", "").strip().lower()
        if Usuario.objects.filter(email=email).exists():
            raise ValidationError("Ya existe un usuario registrado con ese correo.")
        return email

    def clean_cedula(self):
        cedula = self.cleaned_data.get("cedula", "").strip()
        if not re.fullmatch(r"\d{10}", cedula):
            raise ValidationError("La cedula debe tener exactamente 10 numeros.")
        if Usuario.objects.filter(cedula=cedula).exists():
            raise ValidationError("Ya existe un usuario registrado con esa cedula.")
        return cedula

    def clean_telefono(self):
        telefono = self.cleaned_data.get("telefono", "")
        if not re.fullmatch(r"\d{10}", telefono):
            raise ValidationError("El telefono debe tener exactamente 10 numeros.")
        return telefono

    def clean(self):
        cleaned_data = super().clean()
        tipo_usuario = cleaned_data.get("tipo_usuario")
        codigo = cleaned_data.get("codigo_verificacion_profesor")

        if tipo_usuario == "profesor" and codigo != self.CODIGO_PROFESOR:
            self.add_error(
                "codigo_verificacion_profesor",
                "Codigo de verificacion de profesor invalido.",
            )

        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            widget = field.widget
            current_class = widget.attrs.get("class", "")
            if isinstance(
                widget,
                (forms.TextInput, forms.EmailInput, forms.PasswordInput, forms.Select),
            ):
                widget.attrs["class"] = f"{current_class} form-control".strip()
            if isinstance(widget, forms.Select):
                widget.attrs["class"] = f"{current_class} form-select".strip()


class PrimerIngresoPasswordForm(PasswordChangeForm):
    carrera = forms.ChoiceField(
        label="Carrera principal",
        choices=Usuario.CARRERA_CHOICES,
        widget=forms.Select(attrs={"class": "form-select"}),
    )
    carreras = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    old_password = forms.CharField(
        label="Contrasena actual",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    new_password1 = forms.CharField(
        label="Nueva contrasena",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )
    new_password2 = forms.CharField(
        label="Confirmar nueva contrasena",
        widget=forms.PasswordInput(attrs={"class": "form-control"}),
    )

    def __init__(self, user, *args, **kwargs):
        super().__init__(user, *args, **kwargs)
        self.fields["carrera"].initial = Usuario.normalize_carrera(
            getattr(user, "carrera", "")
        )
        self.fields["carreras"].initial = "|".join(user.get_carreras())

    def clean(self):
        cleaned_data = super().clean()
        carrera = cleaned_data.get("carrera")
        raw_carreras = cleaned_data.get("carreras", "")

        if self.user.tipo_usuario == "profesor":
            careers = [
                Usuario.normalize_carrera(item)
                for item in raw_carreras.split("|")
                if Usuario.normalize_carrera(item)
            ]
            if carrera and carrera not in careers:
                careers.insert(0, carrera)
            careers = Usuario.normalize_carreras(careers)
            if not careers:
                self.add_error("carrera", "Debes seleccionar al menos una carrera.")
            cleaned_data["career_list"] = careers
        else:
            cleaned_data["career_list"] = [carrera] if carrera else []

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_carreras(self.cleaned_data["career_list"])
        if commit:
            user.save()
        return user
