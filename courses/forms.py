from django import forms

from .models import CourseActivity


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
