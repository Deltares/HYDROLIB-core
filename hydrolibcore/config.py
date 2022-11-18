from pydantic import BaseSettings


class Settings(BaseSettings):
    """Configuration management, can be derived from ENV of .env file."""

    FM_EXECUTABLE: str = "fm.exe"


# TODO maybe delay init untill model init?
settings = Settings()
