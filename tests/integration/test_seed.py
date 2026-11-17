import os
from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

import pytest
import respx

from app.adapters.outbound.postgres.repository import PostgresWeatherRepository
from app.config import Settings, get_settings
from scripts.seed import seed


def test_seed_is_idempotent_and_does_not_call_openweather(
    repository: PostgresWeatherRepository,
    clear_weather_readings,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    database_url = os.environ.get("TEST_DATABASE_URL") or Settings().test_database_url
    monkeypatch.setenv("DATABASE_URL", database_url)
    get_settings.cache_clear()

    with respx.mock(assert_all_mocked=True):
        seed()
        seed()

    readings, total = repository.list_readings(None, None, 1, 20)
    expected = {
        "São Paulo": (UUID("00000000-0000-4000-8000-000000000001"), Decimal("22.50")),
        "Rio de Janeiro": (
            UUID("00000000-0000-4000-8000-000000000002"),
            Decimal("28.00"),
        ),
        "Curitiba": (UUID("00000000-0000-4000-8000-000000000003"), Decimal("18.00")),
    }

    assert total == 3
    assert {
        reading.city_name: (reading.id, reading.temperature_c) for reading in readings
    } == expected
    assert {reading.country_code for reading in readings} == {"BR"}
    assert {reading.source for reading in readings} == {"openweather"}
    assert {reading.weather_description for reading in readings} == {"seed data"}
    assert {reading.observed_at for reading in readings} == {
        datetime(2026, 1, 1, 12, 0, tzinfo=UTC)
    }
    assert {reading.fetched_at for reading in readings} == {datetime(2026, 1, 1, 12, 0, tzinfo=UTC)}
