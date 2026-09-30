"""File validation and URL signing."""
import time
from typing import Optional

import jwt

from backend.utils.config import settings
from cloud import storage_service

# magic-byte signatures -> (extension, content type)
def detect_type(data: bytes):
    if data.startswith(b"\xff\xd8\xff"):
        return "jpg", "image/jpeg"
    if data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png", "image/png"
    if data[:4] == b"GIF8":
        return "gif", "image/gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return "webp", "image/webp"
    if data.startswith(b"%PDF"):
        return "pdf", "application/pdf"
    return None


def file_url(file_id: Optional[str], storage_key: Optional[str]) -> Optional[str]:
    """Return a time-limited URL. S3 -> presigned URL; local -> our signed-token endpoint."""
    if not file_id or not storage_key:
        return None
    presigned = storage_service.get_storage().presigned_url(storage_key, settings.SIGNED_URL_SECONDS)
    if presigned:
        return presigned
    token = jwt.encode({"fid": file_id, "typ": "file", "exp": int(time.time()) + settings.SIGNED_URL_SECONDS},
                       settings.SECRET_KEY, algorithm="HS256")
    return f"/api/files/content/{token}"
