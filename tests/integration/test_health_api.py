import pytest
from fastapi.testclient import TestClient

from app.adapters.outbound.postgres.repository import PostgresWeatherRepository
from app.domain.errors import DatabaseUnavailable


def test_health_returns_ok_when_database_is_available(client, clear_weather_readings) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "database": "ok"}


def test_health_returns_database_unavailable_when_repository_fails(
    client: TestClient, clear_weather_readings, monkeypatch: pytest.MonkeyPatch
) -> None:
    def fail_health_check(self: PostgresWeatherRepository) -> None:
        raise DatabaseUnavailable

    monkeypatch.setattr(PostgresWeatherRepository, "check_health", fail_health_check)

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"error": "database_unavailable", "details": {}}
