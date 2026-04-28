import json

from django import forms
from django.core.exceptions import ValidationError

from courses.models import Course

from .models import Question, Test


QUESTION_TYPE_LABELS = dict(Question.QUESTION_TYPES)
OPTION_BASED_TYPES = {"multiple_choice", "checkboxes", "dropdown"}
TEXT_BASED_TYPES = {"short_text", "long_text"}


class TestForm(forms.Form):
    def __init__(self, *args, **kwargs):
        test = kwargs.pop("test")
        super().__init__(*args, **kwargs)

        questions = Question.objects.filter(test=test).prefetch_related("answers")
        self.question_map = {question.id: question for question in questions}

        for question in questions:
            field_name = f"question_{question.id}"
            common = {
                "label": question.text,
                "required": question.required,
                "help_text": QUESTION_TYPE_LABELS.get(question.question_type, ""),
            }

            if question.question_type == "short_text":
                self.fields[field_name] = forms.CharField(
                    widget=forms.TextInput(attrs={"class": "form-control"}),
                    **common,
                )
            elif question.question_type == "long_text":
                self.fields[field_name] = forms.CharField(
                    widget=forms.Textarea(
                        attrs={"class": "form-control", "rows": 4}
                    ),
                    **common,
                )
            elif question.question_type == "multiple_choice":
                self.fields[field_name] = forms.ChoiceField(
                    choices=[(answer.id, answer.text) for answer in question.answers.all()],
                    widget=forms.RadioSelect(attrs={"class": "list-clean vstack gap-2"}),
                    **common,
                )
            elif question.question_type == "checkboxes":
                self.fields[field_name] = forms.MultipleChoiceField(
                    choices=[(answer.id, answer.text) for answer in question.answers.all()],
                    widget=forms.CheckboxSelectMultiple(
                        attrs={"class": "list-clean vstack gap-2"}
                    ),
                    **common,
                )
            elif question.question_type == "dropdown":
                self.fields[field_name] = forms.ChoiceField(
                    choices=[("", "Seleccione una opcion"), *[
                        (answer.id, answer.text) for answer in question.answers.all()
                    ]],
                    widget=forms.Select(attrs={"class": "form-select"}),
                    **common,
                )


class TeacherTestForm(forms.ModelForm):
    course = forms.ModelChoiceField(queryset=Course.objects.none(), required=False)
    questions_payload = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = Test
        fields = [
            "name",
            "type",
            "course",
            "description",
            "duration",
            "passing_score",
            "available_date",
            "opening_time",
            "closing_time",
            "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
            "available_date": forms.DateInput(attrs={"type": "date"}),
            "opening_time": forms.TimeInput(attrs={"type": "time", "step": 60}),
            "closing_time": forms.TimeInput(attrs={"type": "time", "step": 60}),
        }

    def __init__(self, *args, **kwargs):
        self.course_context = kwargs.pop("course_context", False)
        course_queryset = kwargs.pop("course_queryset", None)
        initial_course = kwargs.pop("initial_course", None)
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            widget = field.widget
            current_class = widget.attrs.get("class", "")
            if isinstance(widget, (forms.TextInput, forms.NumberInput, forms.Textarea)):
                widget.attrs["class"] = f"{current_class} form-control".strip()
            elif isinstance(widget, forms.Select):
                widget.attrs["class"] = f"{current_class} form-select".strip()
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = f"{current_class} form-check-input".strip()
            elif isinstance(widget, (forms.DateInput, forms.TimeInput)):
                widget.attrs["class"] = f"{current_class} form-control".strip()

        self.fields["type"].choices = [
            ("conocimientos", "Diagnostico"),
            ("vocacional", "Vocacional"),
        ]

        if self.course_context:
            self.fields["course"].label = "Curso"
            self.fields["course"].required = True
            if course_queryset is not None:
                self.fields["course"].queryset = course_queryset
            if initial_course and not self.instance.pk:
                self.fields["course"].initial = initial_course
            self.fields.pop("type")
        else:
            self.fields["type"].label = "Tipo de test"
            self.fields.pop("course")

        if self.instance.pk:
            payload = []
            for question in self.instance.questions.prefetch_related("answers"):
                options = [
                    {
                        "text": answer.text,
                        "is_correct": answer.is_correct,
                    }
                    for answer in question.answers.all()
                ]
                payload.append(
                    {
                        "id": question.id,
                        "text": question.text,
                        "question_type": question.question_type,
                        "required": question.required,
                        "options": options,
                    }
                )
            self.fields["questions_payload"].initial = json.dumps(payload, ensure_ascii=True)
        else:
            self.fields["questions_payload"].initial = "[]"

    def clean(self):
        cleaned_data = super().clean()
        opening_time = cleaned_data.get("opening_time")
        closing_time = cleaned_data.get("closing_time")

        if opening_time and closing_time and opening_time >= closing_time:
            self.add_error(
                "closing_time",
                "La hora de cierre debe ser posterior a la hora de apertura.",
            )

        return cleaned_data

    def clean_questions_payload(self):
        payload = self.cleaned_data.get("questions_payload", "[]")
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise ValidationError("No se pudo interpretar la estructura del formulario.") from exc

        if not isinstance(parsed, list) or not parsed:
            raise ValidationError("Debes agregar al menos una pregunta.")

        normalized_questions = []

        for index, raw_question in enumerate(parsed, start=1):
            if not isinstance(raw_question, dict):
                raise ValidationError(f"La pregunta {index} no tiene un formato valido.")

            text = str(raw_question.get("text", "")).strip()
            question_type = str(raw_question.get("question_type", "")).strip()
            required = bool(raw_question.get("required", True))
            raw_options = raw_question.get("options", [])

            if not text:
                raise ValidationError(f"La pregunta {index} debe tener un enunciado.")

            if question_type not in QUESTION_TYPE_LABELS:
                raise ValidationError(f"La pregunta {index} tiene un tipo no permitido.")

            if question_type in OPTION_BASED_TYPES:
                options = self._clean_option_question(index, question_type, raw_options)
            else:
                options = self._clean_text_question(index, question_type, raw_options)

            normalized_questions.append(
                {
                    "text": text,
                    "question_type": question_type,
                    "required": required,
                    "answers": options,
                }
            )

        self.parsed_questions = normalized_questions
        return payload

    def save(self, commit=True):
        test = super().save(commit=False)
        if self.course_context:
            test.type = "curso"
        if commit:
            test.save()
        return test

    def _clean_option_question(self, index, question_type, raw_options):
        if not isinstance(raw_options, list):
            raise ValidationError(
                f"La pregunta {index} debe incluir una lista de opciones."
            )

        options = []
        correct_count = 0

        for option_index, raw_option in enumerate(raw_options, start=1):
            text = str(raw_option.get("text", "")).strip()
            if not text:
                continue
            is_correct = bool(raw_option.get("is_correct", False))
            correct_count += 1 if is_correct else 0
            options.append(
                {
                    "text": text,
                    "is_correct": is_correct,
                    "order": option_index,
                }
            )

        if len(options) < 2:
            raise ValidationError(
                f"La pregunta {index} debe tener al menos dos opciones."
            )

        if question_type == "checkboxes":
            if correct_count < 1:
                raise ValidationError(
                    f"La pregunta {index} debe tener al menos una opcion correcta."
                )
        elif correct_count != 1:
            raise ValidationError(
                f"La pregunta {index} debe tener exactamente una opcion correcta."
            )

        return options

    def _clean_text_question(self, index, question_type, raw_options):
        if not isinstance(raw_options, list):
            raise ValidationError(
                f"La pregunta {index} debe incluir la respuesta esperada."
            )

        options = []
        for option_index, raw_option in enumerate(raw_options, start=1):
            text = str(raw_option.get("text", "")).strip()
            if not text:
                continue
            options.append(
                {
                    "text": text,
                    "is_correct": option_index == 1,
                    "order": option_index,
                }
            )

        if not options:
            label = "respuesta esperada" if question_type == "short_text" else "guia de respuesta"
            raise ValidationError(
                f"La pregunta {index} debe incluir una {label}."
            )

        return options
