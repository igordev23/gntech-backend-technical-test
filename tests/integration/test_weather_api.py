from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import httpx
import pytest
import respx

from app.adapters.outbound.postgres.repository import PostgresWeatherRepository
from app.domain.models import WeatherReading

GEOCODING_URL = "https://api.openweathermap.org/geo/1.0/direct"
CURRENT_WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"
PUBLIC_READING_FIELDS = {
    "id",
    "city_name",
    "country_code",
    "latitude",
    "longitude",
    "temperature_c",
    "feels_like_c",
    "humidity",
    "pressure_hpa",
    "wind_speed_ms",
    "weather_main",
    "weather_description",
    "observed_at",
    "fetched_at",
    "source",
}


def make_reading(city_name: str, observed_at: datetime) -> WeatherReading:
    return WeatherReading(
        id=uuid4(),
        city_name=city_name,
        country_code="BR",
        latitude=Decimal("-23.550520"),
        longitude=Decimal("-46.633308"),
        temperature_c=Decimal("22.50"),
        feels_like_c=None,
        humidity=70,
        pressure_hpa=1013,
        wind_speed_ms=None,
        weather_main="Clouds",
        weather_description="nuvens dispersas",
        observed_at=observed_at,
        fetched_at=observed_at,
        source="openweather",
        raw_payload={"internal": True},
    )


def mock_weather_sync(router: respx.MockRouter) -> tuple[respx.Route, respx.Route]:
    geocoding = router.get(GEOCODING_URL).mock(
        return_value=httpx.Response(
            200,
            json=[
                {
                    "name": "São Paulo",
                    "country": "BR",
                    "lat": -23.55,
                    "lon": -46.63,
                }
            ],
        )
    )
    current = router.get(CURRENT_WEATHER_URL).mock(
        return_value=httpx.Response(
            200,
            json={
                "name": "São Paulo",
                "sys": {"country": "BR"},
                "coord": {"lat": -23.55, "lon": -46.63},
                "main": {
                    "temp": 22.5,
                    "feels_like": 23,
                    "humidity": 70,
                    "pressure": 1013,
                },
                "wind": {"speed": 3.2},
                "weather": [{"main": "Clouds", "description": "nuvens dispersas"}],
                "dt": 1794942000,
            },
        )
    )
    return geocoding, current


def assert_public_reading(reading: dict[str, object]) -> None:
    assert set(reading) == PUBLIC_READING_FIELDS
    assert "raw_payload" not in reading


def test_sync_persists_and_returns_public_weather_reading(client, clear_weather_readings) -> None:
    with respx.mock(assert_all_mocked=True) as router:
        geocoding, current = mock_weather_sync(router)
        response = client.post(
            "/api/v1/weather/sync",
            json={"city": " São Paulo ", "country": "br"},
        )

    assert response.status_code == 200
    reading = response.json()
    assert_public_reading(reading)
    assert reading["city_name"] == "São Paulo"
    assert reading["country_code"] == "BR"
    assert reading["temperature_c"] == 22.5
    assert reading["observed_at"] == "2026-11-17T19:00:00Z"
    assert dict(geocoding.calls[0].request.url.params) == {
        "q": "São Paulo,BR",
        "limit": "5",
        "appid": "test-key",
    }
    assert dict(current.calls[0].request.url.params) == {
        "lat": "-23.55",
        "lon": "-46.63",
        "appid": "test-key",
        "units": "metric",
        "lang": "pt_br",
    }
    assert geocoding.called
    assert current.called

    listed = client.get("/api/v1/weather", params={"city": "são paulo", "country": "br"})
    assert listed.status_code == 200
    assert listed.json()["total"] == 1
    assert_public_reading(listed.json()["items"][0])


@pytest.mark.parametrize(
    ("method", "path", "payload", "params", "field", "reason"),
    [
        ("post", "/api/v1/weather/sync", {}, None, "city", "required"),
        ("post", "/api/v1/weather/sync", {"city": "  "}, None, "city", "blank"),
        (
            "post",
            "/api/v1/weather/sync",
            {"city": "x" * 121},
            None,
            "city",
            "too_long",
        ),
        (
            "post",
            "/api/v1/weather/sync",
            {"city": "Recife", "country": "B1"},
            None,
            "country",
            "invalid_format",
        ),
        ("get", "/api/v1/weather", None, {"page": 0}, "page", "must_be_positive"),
        ("get", "/api/v1/weather", None, {"page_size": 101}, "page_size", "out_of_range"),
        ("get", "/api/v1/weather", None, {"city": "  "}, "city", "blank"),
    ],
)
def test_invalid_request_uses_stable_validation_error_envelope(
    client,
    clear_weather_readings,
    method: str,
    path: str,
    payload: dict[str, object] | None,
    params: dict[str, object] | None,
    field: str,
    reason: str,
) -> None:
    if method == "post":
        response = client.post(path, json=payload, params=params)
    else:
        response = client.get(path, params=params)

    assert response.status_code == 422
    assert response.json() == {
        "error": "validation_error",
        "details": {"fields": [{"name": field, "reason": reason}]},
    }


def test_sync_without_api_key_returns_provider_not_configured(
    client, clear_weather_readings, monkeypatch: pytest.MonkeyPatch
) -> None:
    from app.config import get_settings

    monkeypatch.setenv("OPENWEATHER_API_KEY", "")
    get_settings.cache_clear()

    response = client.post("/api/v1/weather/sync", json={"city": "Recife"})

    assert response.status_code == 503
    assert response.json() == {"error": "provider_not_configured", "details": {}}


def test_sync_city_not_found_returns_trimmed_query(client, clear_weather_readings) -> None:
    with respx.mock(assert_all_mocked=True) as router:
        route = router.get(GEOCODING_URL).mock(return_value=httpx.Response(200, json=[]))
        response = client.post(
            "/api/v1/weather/sync",
            json={"city": "  Recife  ", "country": "br"},
        )

    assert response.status_code == 404
    assert response.json() == {
        "error": "city_not_found",
        "details": {"city": "Recife", "country": "BR"},
    }
    assert route.called


def test_list_returns_public_items_and_pagination(
    client, repository: PostgresWeatherRepository, clear_weather_readings
) -> None:
    first = make_reading("Recife", datetime(2026, 11, 17, 12, tzinfo=UTC))
    second = make_reading("Curitiba", datetime(2026, 11, 17, 13, tzinfo=UTC))
    repository.upsert(first)
    repository.upsert(second)

    response = client.get("/api/v1/weather", params={"country": "br", "page": 1, "page_size": 1})

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert response.json()["page"] == 1
    assert response.json()["page_size"] == 1
    assert len(response.json()["items"]) == 1
    assert response.json()["items"][0]["city_name"] == "Curitiba"
    assert_public_reading(response.json()["items"][0])


def test_get_by_id_returns_reading_and_missing_id_error(
    client, repository: PostgresWeatherRepository, clear_weather_readings
) -> None:
    reading = repository.upsert(make_reading("Recife", datetime(2026, 11, 17, 12, tzinfo=UTC)))
    missing_id = uuid4()

    response = client.get(f"/api/v1/weather/{reading.id}")
    missing = client.get(f"/api/v1/weather/{missing_id}")

    assert response.status_code == 200
    assert_public_reading(response.json())
    assert response.json()["id"] == str(reading.id)
    assert missing.status_code == 404
    assert missing.json() == {
        "error": "reading_not_found",
        "details": {"id": str(missing_id)},
    }


def test_invalid_uuid_uses_validation_error_envelope(client, clear_weather_readings) -> None:
    response = client.get("/api/v1/weather/not-a-uuid")

    assert response.status_code == 422
    assert response.json() == {
        "error": "validation_error",
        "details": {"fields": [{"name": "id", "reason": "invalid_uuid"}]},
    }


def test_docs_and_openapi_are_available(client) -> None:
    docs = client.get("/docs")
    openapi = client.get("/openapi.json")

    assert docs.status_code == 200
    assert openapi.status_code == 200
    assert "/api/v1/weather/sync" in openapi.json()["paths"]
    assert "/api/v1/weather/{id}" in openapi.json()["paths"]
