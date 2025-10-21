from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Configuration management, can be derived from ENV of .env file."""

    model_config = SettingsConfigDict(
            env_file=".env",            # read from .env if present
            env_file_encoding="utf-8",  # typical default
            extra="ignore"              # ignore unknown env vars
    )

    FM_EXECUTABLE: str = "fm.exe"


settings = Settings()
