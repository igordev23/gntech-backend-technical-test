from dataclasses import replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from app.domain.models import WeatherReading


def make_reading(
    city_name: str,
    temperature: str,
    observed_at: datetime,
    country_code: str = "BR",
) -> WeatherReading:
    return WeatherReading(
        id=uuid4(),
        city_name=city_name,
        country_code=country_code,
        latitude=Decimal("-23.550520"),
        longitude=Decimal("-46.633308"),
        temperature_c=Decimal(temperature),
        feels_like_c=None,
        humidity=70,
        pressure_hpa=1013,
        wind_speed_ms=None,
        weather_main=None,
        weather_description=None,
        observed_at=observed_at,
        fetched_at=observed_at,
        source="openweather",
        raw_payload={"seed": True},
    )


def test_upsert_updates_existing_city_without_creating_duplicate(
    repository, clear_weather_readings
) -> None:
    now = datetime(2026, 11, 17, 12, 0, tzinfo=UTC)
    first = make_reading("Recife", "27.50", now)
    updated = replace(
        first,
        id=uuid4(),
        temperature_c=Decimal("29.00"),
        fetched_at=now + timedelta(minutes=5),
    )

    inserted = repository.upsert(first)
    result = repository.upsert(updated)
    readings, total = repository.list_readings(None, None, 1, 20)

    assert total == 1
    assert len(readings) == 1
    assert result.id == inserted.id
    assert result.temperature_c == Decimal("29.00")


def test_list_readings_filters_and_orders_before_pagination(
    repository, clear_weather_readings
) -> None:
    now = datetime(2026, 11, 17, 12, 0, tzinfo=UTC)
    older = make_reading("Recife", "26.00", now)
    newer = make_reading("São Paulo", "28.00", now + timedelta(hours=1))
    other_city = make_reading("Curitiba", "18.00", now + timedelta(hours=2))
    for reading in (older, newer, other_city):
        repository.upsert(reading)

    readings, total = repository.list_readings(None, "br", 1, 2)

    assert total == 3
    assert [reading.city_name for reading in readings] == ["Curitiba", "São Paulo"]

    next_page, next_total = repository.list_readings(None, "BR", 2, 2)

    assert next_total == 3
    assert [reading.city_name for reading in next_page] == ["Recife"]

    filtered, filtered_total = repository.list_readings("recife", "br", 1, 20)
    assert filtered_total == 1
    assert [reading.city_name for reading in filtered] == ["Recife"]


def test_get_by_id_returns_none_for_unknown_uuid(repository, clear_weather_readings) -> None:
    assert repository.get_by_id(uuid4()) is None


def test_check_health_returns_without_error_when_database_is_available(
    repository, clear_weather_readings
) -> None:
    assert repository.check_health() is None
