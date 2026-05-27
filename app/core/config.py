from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Core application settings.
    Loads configurations from environment variables or a .env file.
    """
    BOT_TOKEN: str
    AITUNNEL_API_KEY: str | None = None
    WEBHOOK_URL: str

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()
