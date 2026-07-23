from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError


ALLOWED_FILE_TYPES = {
    "audio": {"audio/mpeg", "audio/wav", "audio/ogg", "audio/webm"},
    "image": {"image/jpeg", "image/png", "image/webp"},
}


def validate_upload(uploaded_file, category):
    if not uploaded_file:
        return
    if uploaded_file.content_type not in ALLOWED_FILE_TYPES[category]:
        raise ValidationError("Tipo de archivo no permitido.")
    max_size_mb = int(getattr(settings, f"MAX_{category.upper()}_SIZE_MB", 10))
    if uploaded_file.size > max_size_mb * 1024 * 1024:
        raise ValidationError(f"El archivo supera el limite de {max_size_mb} MB.")


def safe_extension(uploaded_file):
    return Path(uploaded_file.name).suffix.lower()[:10]
