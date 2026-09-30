"""Object-storage service. The DB stores metadata + storage_key; the bytes live here.

Backends:
  local -> files under LOCAL_UPLOAD_DIR (free, for simulation)
  s3    -> any S3-compatible bucket (AWS S3, Supabase Storage, Cloudflare R2, MinIO)
Functions required by the assignment: uploadFile() -> upload_file, getFile() -> get_file, deleteFile() -> delete_file.
"""
import logging
import os
from typing import Optional

from backend.utils.config import settings

log = logging.getLogger("storage")


class StorageError(Exception):
    """Raised when the storage backend is unavailable or fails."""


class LocalStorage:
    def _path(self, key: str) -> str:
        root = os.path.abspath(settings.LOCAL_UPLOAD_DIR)
        path = os.path.abspath(os.path.join(root, key))
        if not path.startswith(root + os.sep):  # block path traversal
            raise StorageError("Invalid storage key")
        return path

    def put(self, key, data, content_type):
        try:
            path = self._path(key)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "wb") as f:
                f.write(data)
        except OSError as e:
            raise StorageError(str(e)) from e

    def get(self, key) -> bytes:
        try:
            with open(self._path(key), "rb") as f:
                return f.read()
        except OSError as e:
            raise StorageError(str(e)) from e

    def delete(self, key):
        try:
            os.remove(self._path(key))
        except FileNotFoundError:
            pass
        except OSError as e:
            raise StorageError(str(e)) from e

    def presigned_url(self, key, expires) -> Optional[str]:
        return None  # local files are served through our signed-token endpoint


class S3Storage:
    def __init__(self):
        try:
            import boto3
        except ImportError as e:
            raise StorageError("boto3 is required for STORAGE_BACKEND=s3") from e
        self.bucket = settings.S3_BUCKET
        self.client = boto3.client(
            "s3", region_name=settings.S3_REGION, endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY_ID, aws_secret_access_key=settings.S3_SECRET_ACCESS_KEY)

    def put(self, key, data, content_type):
        try:
            self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        except Exception as e:
            raise StorageError(str(e)) from e

    def get(self, key) -> bytes:
        try:
            return self.client.get_object(Bucket=self.bucket, Key=key)["Body"].read()
        except Exception as e:
            raise StorageError(str(e)) from e

    def delete(self, key):
        try:
            self.client.delete_object(Bucket=self.bucket, Key=key)
        except Exception as e:
            raise StorageError(str(e)) from e

    def presigned_url(self, key, expires) -> Optional[str]:
        # Bucket stays PRIVATE; clients get a time-limited signed URL.
        return self.client.generate_presigned_url(
            "get_object", Params={"Bucket": self.bucket, "Key": key}, ExpiresIn=expires)


def get_storage():
    return S3Storage() if settings.STORAGE_BACKEND == "s3" else LocalStorage()


def upload_file(key: str, data: bytes, content_type: str) -> None:
    get_storage().put(key, data, content_type)


def get_file(key: str) -> bytes:
    return get_storage().get(key)


def delete_file(key: str) -> None:
    get_storage().delete(key)
