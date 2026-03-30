from django import forms

from .models import Question


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
