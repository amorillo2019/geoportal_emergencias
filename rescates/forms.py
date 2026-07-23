from django import forms

from infraestructura.models import Hospital, Shelter
from alertas.models import Alert

from .models import RescueAssignment, RescueTeam, Victim


class RescueAssignmentForm(forms.ModelForm):
    class Meta:
        model = RescueAssignment
        fields = ("team", "notes")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["team"].queryset = RescueTeam.objects.filter(
            operational_status=RescueTeam.OperationalStatus.AVAILABLE
        )


class AssignmentStatusForm(forms.ModelForm):
    class Meta:
        model = RescueAssignment
        fields = ("status", "notes", "outcome")


class VictimForm(forms.ModelForm):
    latitude = forms.DecimalField(required=False, min_value=-90, max_value=90, widget=forms.HiddenInput())
    longitude = forms.DecimalField(required=False, min_value=-180, max_value=180, widget=forms.HiddenInput())

    class Meta:
        model = Victim
        exclude = ("alert", "location", "photo_storage_path")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["transfer_hospital"].queryset = Hospital.objects.filter(is_operational=True)
        self.fields["transfer_shelter"].queryset = Shelter.objects.filter(is_operational=True)

    def clean(self):
        cleaned_data = super().clean()
        destinations = [
            cleaned_data.get("transfer_hospital"),
            cleaned_data.get("transfer_shelter"),
            cleaned_data.get("safe_place"),
        ]
        if sum(bool(destination) for destination in destinations) > 1:
            raise forms.ValidationError("Seleccione un solo destino: hospital, refugio o lugar seguro.")
        return cleaned_data


class GeneralVictimForm(VictimForm):
    alert = forms.ModelChoiceField(
        label="Alerta relacionada", queryset=Alert.objects.order_by("-created_at"), required=False
    )

    def clean(self):
        cleaned_data = super().clean()
        if not cleaned_data.get("alert") and not (cleaned_data.get("latitude") is not None and cleaned_data.get("longitude") is not None):
            raise forms.ValidationError("Sin alerta relacionada, registre la ubicación de la víctima.")
        return cleaned_data
