from django import forms
from django.db.models import Q

from users.models import Usuario

from .models import Classroom, Course, CourseActivity, CourseActivitySubmission


def _failed_diagnostic_students_queryset():
    return (
        Usuario.objects.filter(
            tipo_usuario="estudiante",
            results__test__type="conocimientos",
            results__test__course__isnull=True,
            results__passed=False,
        )
        .exclude(
            results__test__type="conocimientos",
            results__test__course__isnull=True,
            results__passed=True,
        )
        .distinct()
        .order_by("last_name", "first_name", "cedula", "username")
    )


class ClassroomAdminForm(forms.ModelForm):
    class Meta:
        model = Classroom
        fields = ["name", "description", "students", "teachers"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        failed_students = _failed_diagnostic_students_queryset()
        if self.instance.pk:
            failed_students = Usuario.objects.filter(
                Q(id__in=failed_students.values("id")) | Q(classrooms=self.instance)
            ).distinct()
        self.fields["students"].queryset = failed_students
        self.fields["teachers"].queryset = Usuario.objects.filter(
            tipo_usuario="profesor"
        ).order_by("last_name", "first_name", "username")


class CourseAdminForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = [
            "name",
            "classroom",
            "description",
            "welcome_message",
            "teachers",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if "classroom" not in self.fields:
            return

        self.fields["classroom"].required = True
        self.fields["classroom"].label = "Aula de nivelacion"
        self.fields["classroom"].queryset = Classroom.objects.order_by("name")
        self.fields["classroom"].help_text = (
            "Selecciona el aula donde se impartira esta materia de nivelacion."
        )

        if self.instance.pk and self.instance.is_training:
            self.fields["classroom"].required = False

    def clean(self):
        cleaned_data = super().clean()
        classroom = cleaned_data.get("classroom")

        if getattr(self.instance, "is_training", False):
            cleaned_data["classroom"] = None
            return cleaned_data

        if "classroom" in self.fields and not classroom:
            self.add_error(
                "classroom",
                "Selecciona el aula a la que pertenece esta nivelacion.",
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
