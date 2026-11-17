"""Application settings, read from environment variables / backend/.env (never hard-coded).

The database can be configured either with a single DATABASE_URL, or with the
individual DB_HOST / DB_PORT / DB_NAME / DB_USER / DB_PASSWORD values.
If DATABASE_URL is not set, it is built from the individual values.
"""
from urllib.parse import quote_plus

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- Database (Member A) ---
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_NAME: str = ""
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    database_url: str = ""

    # --- AI (Member B) - local Ollama through its OpenAI-compatible API ---
    ai_base_url: str = "http://localhost:11434/v1"
    ai_model: str = "qwen2.5:3b"
    ai_api_key: str = "ollama"                  # Ollama ignores it, but the client requires a value
    ai_timeout_seconds: float = 60.0            # first call loads the model into memory, so allow a cold start
    ai_max_retries: int = 1                     # extra attempts when output fails validation
    ai_max_tokens: int = 800
    ai_require_structured_output: bool = False  # OpenRouter-only routing flag; not used by Ollama
    ai_app_name: str = ""

    # --- Web ---
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    log_level: str = "INFO"

    @model_validator(mode="after")
    def build_database_url(self) -> "Settings":
        if not self.database_url:
            if not (self.DB_NAME and self.DB_USER):
                raise ValueError("Set DATABASE_URL, or DB_NAME/DB_USER/DB_PASSWORD (+ DB_HOST/DB_PORT)")
            self.database_url = (
                f"postgresql+psycopg://{quote_plus(self.DB_USER)}:{quote_plus(self.DB_PASSWORD)}"
                f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            )
        return self

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


settings = Settings()
