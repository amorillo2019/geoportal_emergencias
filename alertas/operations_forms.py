from django import forms

from .models import Alert


class AlertStatusForm(forms.ModelForm):
    class Meta:
        model = Alert
        fields = ("status",)


class AlertPriorityForm(forms.ModelForm):
    class Meta:
        model = Alert
        fields = ("priority",)


class InternalNoteForm(forms.Form):
    observation = forms.CharField(label="Observacion interna", widget=forms.Textarea(attrs={"rows": 3}), max_length=2000)
