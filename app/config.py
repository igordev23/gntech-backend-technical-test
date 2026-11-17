from functools import lru_cache

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_env: str = "development"
    api_port: int = 8000
    log_level: str = "INFO"
    database_url: str = "postgresql+psycopg://weather:weather@localhost:5432/weather"
    test_database_url: str = "postgresql+psycopg://weather:weather@localhost:5432/weather_test"
    openweather_api_key: SecretStr | None = None
    openweather_geocoding_base_url: str = "https://api.openweathermap.org/geo/1.0"
    openweather_base_url: str = "https://api.openweathermap.org/data/2.5"
    openweather_timeout_seconds: float = Field(default=5, gt=0)
    openweather_max_retries: int = Field(default=2, ge=0, le=2)


@lru_cache
def get_settings() -> Settings:
    return Settings()
