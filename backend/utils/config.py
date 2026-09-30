"""Central configuration. Values come from environment variables (see .env.example)."""
import os


class Settings:
    """Reads env vars lazily so tests can change them."""

    @property
    def SECRET_KEY(self) -> str:
        key = os.environ.get("SECRET_KEY")
        if not key:
            raise RuntimeError("SECRET_KEY is not set. Copy .env.example to .env and set it.")
        return key

    def _get(self, name, default):
        return os.environ.get(name, default)

    @property
    def TOKEN_EXPIRE_MINUTES(self): return int(self._get("TOKEN_EXPIRE_MINUTES", "60"))
    @property
    def DATABASE_PATH(self): return self._get("DATABASE_PATH", "data/app.db")
    @property
    def CORS_ORIGINS(self): return [o.strip() for o in self._get("CORS_ORIGINS", "http://localhost:8000").split(",")]
    @property
    def MAX_UPLOAD_BYTES(self): return int(float(self._get("MAX_UPLOAD_MB", "5")) * 1024 * 1024)
    @property
    def RATE_LIMIT_PER_MIN(self): return int(self._get("RATE_LIMIT_PER_MIN", "30"))
    @property
    def SIGNED_URL_SECONDS(self): return int(self._get("SIGNED_URL_SECONDS", "3600"))
    @property
    def STORAGE_BACKEND(self): return self._get("STORAGE_BACKEND", "local").lower()
    @property
    def LOCAL_UPLOAD_DIR(self): return self._get("LOCAL_UPLOAD_DIR", "uploads")
    @property
    def S3_BUCKET(self): return self._get("S3_BUCKET", "")
    @property
    def S3_REGION(self): return self._get("S3_REGION", "us-east-1")
    @property
    def S3_ENDPOINT_URL(self): return self._get("S3_ENDPOINT_URL", "") or None
    @property
    def S3_ACCESS_KEY_ID(self): return self._get("S3_ACCESS_KEY_ID", "") or None
    @property
    def S3_SECRET_ACCESS_KEY(self): return self._get("S3_SECRET_ACCESS_KEY", "") or None


settings = Settings()
