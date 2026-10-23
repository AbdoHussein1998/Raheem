"""Validated runtime configuration shared by API and Celery."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApplicationBasicSettings(BaseSettings):
    APP_NAME: str
    APP_VERSION: str

    OMNI_MONGO_URL: str
    OMNI_MONGO_DB_NAME: str

    OMNI_POSTGRES_HOST: str
    OMNI_POSTGRES_PORT: int
    OMNI_POSTGRES_USER: str
    OMNI_POSTGRES_PASSWORD: str
    OMNI_POSTGRES_DB: str
    # OMNI_POSTGRES_POOL_SIZE: int
    # OMNI_POSTGRES_MAX_OVERFLOW: int
    # OMNI_POSTGRES_POOL_TIMEOUT: int
    # OMNI_POSTGRES_POOL_RECYCLE: int
    OMNI_POSTGRES_ECHO: bool = False

    # OMNI_REDIS_URL: str
    OMNI_MINIO_ENDPOINT: str
    OMNI_MINIO_ACCESS_KEY: str
    OMNI_MINIO_SECRET_KEY: str
    OMNI_MINIO_PDF_BUCKET: str | None = None
    # OMNI_PDF_MAX_UPLOAD_BYTES: int = 25 * 1024 * 1024

    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    CELERY_BROKER_CONNECTUIONS_POOL: int

    JWT_SECRET_KEY: str
    JWT_HASHING_ALGORITHM: str
    # GOOGLE_CLIENT_ID: str
    # GOOGLE_CLIENT_SECRET: str

    # Optional infrastructure, disabled by default as in the original lifespan.
    # ENABLE_LLM: bool = False
    # OMNI_GENERATION_MODEL: str | None = None
    # OMNI_GENERATION_PROVIDER: str = "ollama"
    # OMNI_GENERATION_MODEL_API_KEY: str | None = None
    # OMNI_GENERATION_MODEL_CONNECTION_URL: str | None = None
    # OMNI_EMBEDDING_MODEL: str | None = None
    # OMNI_EMBEDDING_PROVIDER: str = "ollama"
    # OMNI_EMBEDDING_MODEL_API_KEY: str | None = None
    # OMNI_EMBEDDING_MODEL_CONNECTION_URL: str | None = None

    model_config = SettingsConfigDict(env_file="src/.env", extra="ignore")


def get_basic_settings() -> ApplicationBasicSettings:
    return ApplicationBasicSettings()
