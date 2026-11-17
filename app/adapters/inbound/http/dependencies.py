from typing import Annotated

from fastapi import Depends

from app.adapters.outbound.openweather.client import OpenWeatherClient
from app.adapters.outbound.postgres.repository import PostgresWeatherRepository
from app.adapters.outbound.postgres.session import get_session_factory
from app.application.weather_service import WeatherService
from app.config import Settings, get_settings


def get_weather_provider(
    settings: Annotated[Settings, Depends(get_settings)],
) -> OpenWeatherClient:
    return OpenWeatherClient(settings)


def get_weather_repository(
    settings: Annotated[Settings, Depends(get_settings)],
) -> PostgresWeatherRepository:
    return PostgresWeatherRepository(get_session_factory(settings.database_url))


def get_weather_service(
    provider: Annotated[OpenWeatherClient, Depends(get_weather_provider)],
    repository: Annotated[PostgresWeatherRepository, Depends(get_weather_repository)],
) -> WeatherService:
    return WeatherService(provider, repository)
