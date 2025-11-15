from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    app_name: str = Field(default="whatsub-subscriptions")
    app_env: str = Field(default="development")
    log_level: str = Field(default="INFO")
    port: int = Field(default=8080, alias="PORT")
    
    # Database settings
    db_host: str | None = Field(default=None)
    db_port: int = Field(default=3306)
    db_user: str | None = Field(default=None)
    db_pass: str | None = Field(default=None)
    db_name: str | None = Field(default=None)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]

