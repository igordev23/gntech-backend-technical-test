from dataclasses import is_dataclass
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from app.domain.models import WeatherReading


def test_weather_reading_preserves_typed_provider_values() -> None:
    observed_at = datetime(2026, 11, 17, 12, 0, tzinfo=UTC)
    reading = WeatherReading(
        id=uuid4(),
        city_name="São Paulo",
        country_code="BR",
        latitude=Decimal("-23.550520"),
        longitude=Decimal("-46.633308"),
        temperature_c=Decimal("22.50"),
        feels_like_c=Decimal("23.00"),
        humidity=70,
        pressure_hpa=1013,
        wind_speed_ms=Decimal("3.20"),
        weather_main="Clouds",
        weather_description="nuvens dispersas",
        observed_at=observed_at,
        fetched_at=observed_at,
        source="openweather",
        raw_payload={"main": {"temp": 22.5}},
    )

    assert is_dataclass(reading)
    assert reading.city_name == "São Paulo"
    assert reading.country_code == "BR"
    assert reading.temperature_c == Decimal("22.50")
    assert reading.observed_at == observed_at
    assert reading.raw_payload == {"main": {"temp": 22.5}}
