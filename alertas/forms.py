from django import forms

from services.file_validation import validate_upload

from .models import Alert


def validate_audio(uploaded_file):
    validate_upload(uploaded_file, "audio")


def validate_image(uploaded_file):
    validate_upload(uploaded_file, "image")


class PublicAlertForm(forms.ModelForm):
    consent_location = forms.BooleanField(
        label="Usar mi ubicacion para atender la alerta.", required=True
    )
    audio = forms.FileField(label="Audio opcional", required=False, validators=[validate_audio])
    image = forms.FileField(label="Imagen opcional", required=False, validators=[validate_image])

    class Meta:
        model = Alert
        fields = (
            "person_name", "phone", "alternative_phone", "email",
            "latitude", "longitude", "address_reference", "emergency_type",
            "description", "estimated_affected_people", "injured_people",
            "has_children", "has_older_adults", "has_people_with_disabilities",
            "building_condition", "consent_location",
        )
        widgets = {
            "latitude": forms.NumberInput(attrs={"step": "0.000001", "readonly": True}),
            "longitude": forms.NumberInput(attrs={"step": "0.000001", "readonly": True}),
            "description": forms.Textarea(attrs={"rows": 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        latitude = cleaned_data.get("latitude")
        longitude = cleaned_data.get("longitude")
        if latitude is None or longitude is None:
            raise forms.ValidationError("Obtenga la ubicacion antes de enviar la alerta.")
        return cleaned_data
