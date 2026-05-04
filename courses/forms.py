from django import forms

from users.models import Usuario

from .models import Course, CourseActivity, CourseActivitySubmission


class CourseAdminForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            "name",
            "career",
            "description",
            "welcome_message",
            "teachers",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "career" not in self.fields:
            return

        careers = sorted(
            {
                career
                for career in Usuario.objects.exclude(carrera="")
                .values_list("carrera", flat=True)
                if career
            },
            key=str.casefold,
        )
        current_career = Usuario.normalize_carrera(
            getattr(self.instance, "career", "")
        )
        if current_career and current_career not in careers:
            careers.append(current_career)
            careers.sort(key=str.casefold)

        self.fields["career"].required = False
        self.fields["career"].label = "Carrera de la nivelacion"
        self.fields["career"].widget = forms.Select(
            choices=[
                ("", "Seleccione una carrera"),
                *[(career, career) for career in careers],
            ]
        )
        self.fields["career"].help_text = (
            "Las carreras se cargan automaticamente desde los estudiantes y profesores importados."
        )

    def clean_career(self):
        return Usuario.normalize_carrera(self.cleaned_data.get("career", ""))

    def clean(self):
        cleaned_data = super().clean()
        career = cleaned_data.get("career", "")

        if getattr(self.instance, "is_training", False):
            cleaned_data["career"] = ""
            return cleaned_data

        if "career" in self.fields and not career:
            self.add_error(
                "career",
                "Selecciona la carrera a la que pertenece esta nivelacion.",
            )

        return cleaned_data


class CourseActivityForm(forms.ModelForm):
    class Meta:
        model = CourseActivity
        fields = [
            "title",
            "description",
            "url",
            "attachment",
            "due_date",
            "opening_time",
            "closing_time",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 4}),
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "opening_time": forms.TimeInput(attrs={"type": "time", "step": 60}),
            "closing_time": forms.TimeInput(attrs={"type": "time", "step": 60}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            current_class = widget.attrs.get("class", "")
            if isinstance(
                widget,
                (
                    forms.TextInput,
                    forms.DateInput,
                    forms.TimeInput,
                    forms.URLInput,
                    forms.ClearableFileInput,
                    forms.Textarea,
                ),
            ):
                widget.attrs["class"] = f"{current_class} form-control".strip()


class CourseActivitySubmissionForm(forms.ModelForm):
    class Meta:
        model = CourseActivitySubmission
        fields = [
            "submission_text",
            "submission_url",
            "attachment",
        ]
        widgets = {
            "submission_text": forms.Textarea(attrs={"rows": 2}),
            "submission_url": forms.URLInput(attrs={"placeholder": "https://..."}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            current_class = widget.attrs.get("class", "")
            if isinstance(
                widget,
                (
                    forms.TextInput,
                    forms.URLInput,
                    forms.ClearableFileInput,
                    forms.Textarea,
                ),
            ):
                widget.attrs["class"] = f"{current_class} form-control".strip()

    def clean(self):
        cleaned_data = super().clean()
        if (
            not cleaned_data.get("submission_text")
            and not cleaned_data.get("submission_url")
            and not cleaned_data.get("attachment")
        ):
            raise forms.ValidationError(
                "Debes cargar un archivo, URL o comentario para registrar la entrega."
            )
        return cleaned_data


class CourseActivityGradeForm(forms.ModelForm):
    class Meta:
        model = CourseActivitySubmission
        fields = [
            "grade",
            "teacher_comment",
        ]
        widgets = {
            "grade": forms.NumberInput(
                attrs={
                    "step": "0.01",
                    "min": "0",
                    "max": "100",
                    "placeholder": "0 - 100",
                }
            ),
            "teacher_comment": forms.Textarea(attrs={"rows": 2}),
        }
        labels = {
            "grade": "Calificacion",
            "teacher_comment": "Comentario del profesor",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            current_class = widget.attrs.get("class", "")
            if isinstance(
                widget,
                (
                    forms.NumberInput,
                    forms.TextInput,
                    forms.Textarea,
                ),
            ):
                widget.attrs["class"] = f"{current_class} form-control".strip()


class CourseClassSessionForm(forms.Form):
    class_dates = forms.CharField(
        widget=forms.Textarea(
            attrs={
                "rows": 3,
                "placeholder": "2026-05-01, 2026-05-08, 2026-05-15",
            }
        ),
        label="Fechas de clase",
        help_text="Ingresa fechas separadas por comas en formato YYYY-MM-DD.",
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["class_dates"].widget.attrs["class"] = "form-control"
