"""Application settings, read from environment variables / .env (never hard-coded).

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

    # --- AI (Member B) - any OpenAI-compatible endpoint; OpenRouter by default ---
    ai_base_url: str = "https://openrouter.ai/api/v1"
    ai_model: str = "openrouter/free"          # or a specific "<vendor>/<model>:free" id
    ai_api_key: str = ""                        # set in .env only, never commit it
    ai_timeout_seconds: float = 45.0
    ai_max_retries: int = 1                     # extra attempts when output fails validation
    ai_max_tokens: int = 1500                   # room for "thinking" models to reason AND answer
    ai_require_structured_output: bool = True   # only route to providers that support JSON schema
    ai_app_name: str = "EY Helpdesk Capstone"   # label shown in your OpenRouter activity page

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


settings = Settings()
