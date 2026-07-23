from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, override_settings

from .file_validation import validate_upload
from .supabase_storage import StorageError, SupabaseStorage


class StorageValidationTests(SimpleTestCase):
    def test_rejects_invalid_mime_type(self):
        upload = SimpleUploadedFile("file.exe", b"x", content_type="application/octet-stream")
        with self.assertRaises(ValidationError):
            validate_upload(upload, "image")

    @override_settings(SUPABASE_URL="", SUPABASE_SERVICE_ROLE_KEY="")
    def test_storage_requires_backend_credentials(self):
        with self.assertRaises(StorageError):
            SupabaseStorage()
