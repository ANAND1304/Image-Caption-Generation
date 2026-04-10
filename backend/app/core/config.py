from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        protected_namespaces=("settings_",),
    )

    app_name: str = "CaptionAI"
    version: str = "2.0.0"
    debug: bool = False
    secret_key: str = "dev-secret-key"
    redis_url: str = "redis://localhost:6379"
    cache_ttl_seconds: int = 3600
    beam_size: int = 3
    max_image_size_mb: int = 10
    allowed_content_types: list[str] = [
        "image/jpeg", "image/png", "image/webp", "image/gif"
    ]
    allowed_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
    ]

    @property
    def max_image_size_bytes(self) -> int:
        return self.max_image_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()