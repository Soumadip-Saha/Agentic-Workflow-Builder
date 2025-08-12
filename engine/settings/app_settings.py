import logging
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

class AppSettings(BaseSettings):
    """
    Centralized settings. API keys are loaded if present but are not required
    for the application to start. They are validated at runtime when used.
    """
    # By setting the default to None, the fields become OPTIONAL.
    # Pydantic will not raise an error if the environment variable is missing.
    openai_api_key: str | None = Field(default=None, alias='OPENAI_API_KEY')
    google_api_key: str | None = Field(default=None, alias='GOOGLE_API_KEY')
    self_hosted_api_key: str | None = Field(default=None, alias='SELF_HOSTED_API_KEY')

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore'
    )

try:
    settings = AppSettings()
    logging.info("Application settings loaded. Found keys for: " + 
                 ("OpenAI " if settings.openai_api_key else "") + 
                 ("Google " if settings.google_api_key else ""))
except Exception as e:
    # This block is now less likely to be hit, but is good for catching
    # file-related or other unexpected errors.
    logging.critical(f"FATAL ERROR during settings initialization: {e}")
    raise SystemExit(f"Configuration Error: {e}") from e