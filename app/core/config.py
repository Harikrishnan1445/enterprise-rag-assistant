from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Enterprise Knowledge Intelligence & RAG Assistant"
    environment: str = "development"

    database_url: str
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    max_upload_size_mb: int = 20
    storage_path: str = "storage/documents"
    allowed_file_types: str = "pdf,docx,txt"

settings = Settings()