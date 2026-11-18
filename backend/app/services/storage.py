from pathlib import Path
from uuid import uuid4
from app.core.config import get_settings

class DocumentStorageError(RuntimeError):
    pass

class DocumentStorage:
    def __init__(self):
        self.settings = get_settings()

    def save(self, content: bytes, filename: str, content_type: str) -> str:
        key = f'{uuid4().hex}{Path(filename).suffix.lower()}'
        if self.settings.minio_endpoint:
            try:
                from minio import Minio
                from minio.error import MinioException
            except ImportError as exc:
                raise DocumentStorageError('Configured MinIO storage is unavailable.') from exc
            try:
                client = Minio(self.settings.minio_endpoint, access_key=self.settings.minio_access_key, secret_key=self.settings.minio_secret_key, secure=self.settings.minio_secure)
                if not client.bucket_exists(self.settings.minio_bucket):
                    client.make_bucket(self.settings.minio_bucket)
                from io import BytesIO
                client.put_object(self.settings.minio_bucket, key, BytesIO(content), len(content), content_type=content_type)
            except (MinioException, OSError) as exc:
                raise DocumentStorageError('Configured MinIO storage is unavailable.') from exc
        else:
            try:
                root = Path('uploads')
                root.mkdir(exist_ok=True)
                (root / key).write_bytes(content)
            except OSError as exc:
                raise DocumentStorageError('Local document storage is unavailable.') from exc
        return key

storage = DocumentStorage()
