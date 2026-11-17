"""Application settings, read from environment variables / .env (never hard-coded).

Member A owns this file (F1.2). If A already has a Settings class, add the
"AI" block below to it instead of replacing the file.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str

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


settings = Settings()
