from django import forms

from .models import CourseActivity, CourseActivitySubmission


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
