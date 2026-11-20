"""Validated runtime configuration shared by API and Temporal workers."""
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

    # Retained temporarily for existing welcome Celery endpoint.
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None
    CELERY_BROKER_CONNECTUIONS_POOL: int = 10

    TEMPORAL_ADDRESS: str = "localhost:7233"
    TEMPORAL_NAMESPACE: str = "default"
    TEMPORAL_PDF_TASK_QUEUE: str = "pdf-processing"
    TEMPORAL_TLS: bool = False
    TEMPORAL_API_KEY: str | None = None
    TEMPORAL_MAX_PDF_CONVERSIONS: int = 1
    OMNI_PDF_MAX_UPLOAD_BYTES: int = 60 * 1024 * 1024

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
