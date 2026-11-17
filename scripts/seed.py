from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from app.adapters.outbound.postgres.repository import PostgresWeatherRepository
from app.adapters.outbound.postgres.session import get_session_factory
from app.config import get_settings
from app.domain.models import WeatherReading


def seed() -> None:
    settings = get_settings()
    repository = PostgresWeatherRepository(get_session_factory(settings.database_url))
    for reading in _seed_readings():
        repository.upsert(reading)


def _seed_readings() -> tuple[WeatherReading, ...]:
    fetched_at = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    return (
        WeatherReading(
            id=UUID("00000000-0000-4000-8000-000000000001"),
            city_name="São Paulo",
            country_code="BR",
            latitude=Decimal("-23.550520"),
            longitude=Decimal("-46.633308"),
            temperature_c=Decimal("22.50"),
            feels_like_c=Decimal("22.50"),
            humidity=65,
            pressure_hpa=1013,
            wind_speed_ms=Decimal("2.50"),
            weather_main="Clear",
            weather_description="seed data",
            observed_at=fetched_at,
            fetched_at=fetched_at,
            source="openweather",
            raw_payload={"seed": True},
        ),
        WeatherReading(
            id=UUID("00000000-0000-4000-8000-000000000002"),
            city_name="Rio de Janeiro",
            country_code="BR",
            latitude=Decimal("-22.906847"),
            longitude=Decimal("-43.172897"),
            temperature_c=Decimal("28.00"),
            feels_like_c=Decimal("29.00"),
            humidity=70,
            pressure_hpa=1012,
            wind_speed_ms=Decimal("3.00"),
            weather_main="Clouds",
            weather_description="seed data",
            observed_at=fetched_at,
            fetched_at=fetched_at,
            source="openweather",
            raw_payload={"seed": True},
        ),
        WeatherReading(
            id=UUID("00000000-0000-4000-8000-000000000003"),
            city_name="Curitiba",
            country_code="BR",
            latitude=Decimal("-25.428400"),
            longitude=Decimal("-49.273300"),
            temperature_c=Decimal("18.00"),
            feels_like_c=Decimal("18.00"),
            humidity=60,
            pressure_hpa=1015,
            wind_speed_ms=Decimal("2.00"),
            weather_main="Clear",
            weather_description="seed data",
            observed_at=fetched_at,
            fetched_at=fetched_at,
            source="openweather",
            raw_payload={"seed": True},
        ),
    )


if __name__ == "__main__":
    seed()
