import secrets

from django.conf import settings


class StorageError(RuntimeError):
    pass


class SupabaseStorage:
    """Backend-only adapter for Supabase Storage."""

    def __init__(self, bucket=None):
        url = getattr(settings, "SUPABASE_URL", "")
        key = getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "")
        if not url or not key:
            raise StorageError("Supabase Storage no esta configurado en el entorno.")
        try:
            from supabase import create_client
            self.client = create_client(url, key)
        except Exception as exc:
            raise StorageError("No se pudo inicializar Supabase Storage.") from exc
        self.bucket = bucket or getattr(settings, "SUPABASE_STORAGE_BUCKET", "emergency-evidence")

    def upload(self, uploaded_file, folder, filename):
        path = f"{folder.strip('/')}/{secrets.token_hex(8)}-{filename}"
        try:
            self.client.storage.from_(self.bucket).upload(
                path, uploaded_file.read(),
                file_options={"content-type": uploaded_file.content_type, "upsert": "false"},
            )
        except Exception as exc:
            raise StorageError("No se pudo cargar el archivo en Supabase Storage.") from exc
        return path

    def delete(self, path):
        try:
            self.client.storage.from_(self.bucket).remove([path])
        except Exception as exc:
            raise StorageError("No se pudo eliminar el archivo de Supabase Storage.") from exc

    def signed_url(self, path, expires_in=300):
        try:
            response = self.client.storage.from_(self.bucket).create_signed_url(path, expires_in)
            return response.get("signedURL") or response.get("signedUrl")
        except Exception as exc:
            raise StorageError("No se pudo generar la URL segura.") from exc
