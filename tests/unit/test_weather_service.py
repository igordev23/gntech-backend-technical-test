from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest

from app.application.weather_service import WeatherService
from app.domain.errors import CityNotFound, ReadingNotFound
from app.domain.models import WeatherReading


def make_reading() -> WeatherReading:
    timestamp = datetime(2026, 11, 17, 12, 0, tzinfo=UTC)
    return WeatherReading(
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
        observed_at=timestamp,
        fetched_at=timestamp,
        source="openweather",
        raw_payload={},
    )


class FakeProvider:
    def __init__(self, reading: WeatherReading | None = None, error: Exception | None = None):
        self.reading = reading or make_reading()
        self.error = error
        self.calls: list[tuple[str, str | None]] = []

    def fetch_current(self, city: str, country: str | None) -> WeatherReading:
        self.calls.append((city, country))
        if self.error:
            raise self.error
        return self.reading


class FakeRepository:
    def __init__(self) -> None:
        self.upserted: list[WeatherReading] = []
        self.list_result: tuple[list[WeatherReading], int] = ([], 0)
        self.reading: WeatherReading | None = None

    def upsert(self, reading: WeatherReading) -> WeatherReading:
        self.upserted.append(reading)
        return reading

    def list_readings(
        self, city: str | None, country: str | None, page: int, page_size: int
    ) -> tuple[list[WeatherReading], int]:
        self.list_arguments = (city, country, page, page_size)
        return self.list_result

    def get_by_id(self, reading_id):
        return self.reading

    def check_health(self) -> None:
        return None


def test_sync_weather_fetches_then_upserts_reading() -> None:
    reading = make_reading()
    provider = FakeProvider(reading=reading)
    repository = FakeRepository()
    service = WeatherService(provider, repository)

    result = service.sync_weather(" São Paulo ", "br")

    assert result is reading
    assert provider.calls == [("São Paulo", "BR")]
    assert repository.upserted == [reading]


def test_sync_weather_does_not_upsert_when_city_is_not_found() -> None:
    provider = FakeProvider(error=CityNotFound())
    repository = FakeRepository()
    service = WeatherService(provider, repository)

    with pytest.raises(CityNotFound):
        service.sync_weather("Missing City", None)

    assert repository.upserted == []


def test_list_readings_passes_filters_and_pagination_to_repository() -> None:
    reading = make_reading()
    provider = FakeProvider()
    repository = FakeRepository()
    repository.list_result = ([reading], 1)
    service = WeatherService(provider, repository)

    result = service.list_readings(" São Paulo ", "br", 2, 10)

    assert result == ([reading], 1)
    assert repository.list_arguments == ("São Paulo", "BR", 2, 10)


def test_get_reading_raises_when_repository_has_no_matching_id() -> None:
    service = WeatherService(FakeProvider(), FakeRepository())

    with pytest.raises(ReadingNotFound):
        service.get_reading(uuid4())
