from django import forms
from django.core.exceptions import ValidationError

from .models import Question, Test


class TestForm(forms.Form):
    def __init__(self, *args, **kwargs):
        test = kwargs.pop("test")
        super().__init__(*args, **kwargs)

        for question in Question.objects.filter(test=test).prefetch_related("answers"):
            answers = question.answers.all()
            self.fields[f"question_{question.id}"] = forms.ChoiceField(
                label=question.text,
                choices=[(answer.id, answer.text) for answer in answers],
                widget=forms.RadioSelect,
            )


class TeacherTestForm(forms.ModelForm):
    questions_payload = forms.CharField(
        label="Preguntas y respuestas",
        widget=forms.Textarea(
            attrs={
                "rows": 12,
                "placeholder": (
                    "Formato por linea:\n"
                    "Pregunta|Respuesta correcta*|Respuesta 2|Respuesta 3|Respuesta 4"
                ),
            }
        ),
        help_text=(
            "Marca la respuesta correcta con * y separa cada elemento con |."
        ),
    )

    class Meta:
        model = Test
        fields = [
            "name",
            "type",
            "description",
            "duration",
            "passing_score",
            "is_active",
        ]
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            widget = field.widget
            current_class = widget.attrs.get("class", "")
            if isinstance(widget, (forms.TextInput, forms.NumberInput, forms.Textarea)):
                widget.attrs["class"] = f"{current_class} form-control".strip()
            elif isinstance(widget, forms.Select):
                widget.attrs["class"] = f"{current_class} form-select".strip()
            elif isinstance(widget, forms.CheckboxInput):
                widget.attrs["class"] = f"{current_class} form-check-input".strip()

        if self.instance.pk and self.instance.questions.exists():
            lines = []
            for question in self.instance.questions.prefetch_related("answers"):
                options = []
                for answer in question.answers.all():
                    suffix = "*" if answer.is_correct else ""
                    options.append(f"{answer.text}{suffix}")
                lines.append("|".join([question.text, *options]))
            self.fields["questions_payload"].initial = "\n".join(lines)

    def clean_questions_payload(self):
        payload = self.cleaned_data["questions_payload"]
        parsed_questions = []

        for line_number, raw_line in enumerate(payload.splitlines(), start=1):
            line = raw_line.strip()
            if not line:
                continue

            parts = [part.strip() for part in line.split("|") if part.strip()]
            if len(parts) < 3:
                raise ValidationError(
                    f"La linea {line_number} debe incluir una pregunta y al menos dos respuestas."
                )

            question_text, *raw_answers = parts
            answers = []
            correct_answers = 0

            for raw_answer in raw_answers:
                is_correct = raw_answer.endswith("*")
                answer_text = raw_answer[:-1].strip() if is_correct else raw_answer
                if not answer_text:
                    raise ValidationError(
                        f"La linea {line_number} tiene una respuesta vacia."
                    )
                correct_answers += 1 if is_correct else 0
                answers.append({"text": answer_text, "is_correct": is_correct})

            if correct_answers != 1:
                raise ValidationError(
                    f"La linea {line_number} debe tener exactamente una respuesta correcta."
                )

            parsed_questions.append(
                {
                    "text": question_text,
                    "answers": answers,
                }
            )

        if not parsed_questions:
            raise ValidationError("Debes ingresar al menos una pregunta.")

        self.parsed_questions = parsed_questions
        return payload
