from types import SimpleNamespace

import httpx
import pytest
import respx

from app.adapters.outbound.openweather.client import OpenWeatherClient
from app.domain.errors import (
    CityNotFound,
    ProviderAuthError,
    ProviderInvalidResponse,
    ProviderNotConfigured,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable,
)

GEOCODING_URL = "https://api.openweathermap.org/geo/1.0/direct"
WEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"


def make_client(api_key: str | None = "test-key") -> OpenWeatherClient:
    settings = SimpleNamespace(
        openweather_api_key=api_key,
        openweather_geocoding_base_url="https://api.openweathermap.org/geo/1.0",
        openweather_base_url="https://api.openweathermap.org/data/2.5",
        openweather_timeout_seconds=5,
        openweather_max_retries=2,
    )
    return OpenWeatherClient(settings)


def current_payload() -> dict:
    return {
        "name": "Recife",
        "coord": {"lat": -8.05, "lon": -34.9},
        "sys": {"country": "br"},
        "main": {
            "temp": 27.5,
            "feels_like": 29.0,
            "humidity": 75,
            "pressure": 1012,
        },
        "wind": {"speed": 3.4},
        "weather": [{"main": "Clouds", "description": "nuvens dispersas"}],
        "dt": 1794916800,
    }


def add_successful_geocoding(
    mock: respx.MockRouter, results: list[dict] | None = None
) -> respx.Route:
    return mock.get(GEOCODING_URL).mock(
        return_value=httpx.Response(
            200,
            json=(
                results
                if results is not None
                else [{"name": "Recife", "country": "BR", "lat": -8.05, "lon": -34.9}]
            ),
        )
    )


def test_fetch_current_resolves_country_and_maps_current_weather() -> None:
    with respx.mock(assert_all_called=True) as mock:
        geocoding = add_successful_geocoding(
            mock,
            [
                {"name": "Recife", "country": "US", "lat": 39.5, "lon": -98.3},
                {"name": "Recife", "country": "BR", "lat": -8.05, "lon": -34.9},
            ],
        )
        current = mock.get(WEATHER_URL).mock(
            return_value=httpx.Response(200, json=current_payload())
        )

        reading = make_client().fetch_current("Recife", "br")

    assert dict(geocoding.calls[0].request.url.params) == {
        "q": "Recife,BR",
        "limit": "5",
        "appid": "test-key",
    }
    assert dict(current.calls[0].request.url.params) == {
        "lat": "-8.05",
        "lon": "-34.9",
        "appid": "test-key",
        "units": "metric",
        "lang": "pt_br",
    }
    assert reading.city_name == "Recife"
    assert reading.country_code == "BR"
    assert str(reading.temperature_c) == "27.5"
    assert str(reading.feels_like_c) == "29.0"
    assert reading.humidity == 75
    assert reading.pressure_hpa == 1012
    assert str(reading.wind_speed_ms) == "3.4"
    assert reading.weather_main == "Clouds"
    assert reading.weather_description == "nuvens dispersas"
    assert reading.observed_at.isoformat() == "2026-11-17T12:00:00+00:00"
    assert reading.source == "openweather"
    assert reading.raw_payload == current_payload()


def test_fetch_current_uses_geocoding_fallbacks_without_country() -> None:
    payload = {
        "main": {"temp": 18, "humidity": 60},
        "dt": 1794916800,
    }
    with respx.mock(assert_all_called=True) as mock:
        geocoding = add_successful_geocoding(
            mock, [{"name": "Curitiba", "country": "BR", "lat": -25.43, "lon": -49.27}]
        )
        mock.get(WEATHER_URL).mock(return_value=httpx.Response(200, json=payload))

        reading = make_client().fetch_current("Curitiba", None)

    assert dict(geocoding.calls[0].request.url.params) == {
        "q": "Curitiba",
        "limit": "5",
        "appid": "test-key",
    }
    assert reading.city_name == "Curitiba"
    assert reading.country_code == "BR"
    assert str(reading.latitude) == "-25.43"
    assert str(reading.longitude) == "-49.27"
    assert reading.feels_like_c is None
    assert reading.pressure_hpa is None
    assert reading.wind_speed_ms is None
    assert reading.weather_main is None
    assert reading.weather_description is None


@pytest.mark.parametrize(
    "results",
    [
        [],
        [{"name": "Recife", "country": "US", "lat": 39.5, "lon": -98.3}],
    ],
)
def test_fetch_current_raises_city_not_found_without_matching_location(
    results: list[dict],
) -> None:
    with respx.mock(assert_all_called=True) as mock:
        add_successful_geocoding(mock, results)

        with pytest.raises(CityNotFound):
            make_client().fetch_current("Recife", "BR")


def test_fetch_current_rejects_missing_api_key_without_http_calls() -> None:
    with respx.mock(assert_all_called=True):
        with pytest.raises(ProviderNotConfigured):
            make_client(api_key=None).fetch_current("Recife", "BR")


@pytest.mark.parametrize(
    ("status_code", "error_type", "expected_calls"),
    [
        (401, ProviderAuthError, 1),
        (400, ProviderInvalidResponse, 1),
        (404, ProviderInvalidResponse, 1),
        (429, ProviderRateLimited, 3),
        (503, ProviderUnavailable, 3),
    ],
)
def test_fetch_current_maps_http_errors_and_retries_only_transient_statuses(
    monkeypatch: pytest.MonkeyPatch,
    status_code: int,
    error_type: type[Exception],
    expected_calls: int,
) -> None:
    monkeypatch.setattr("app.adapters.outbound.openweather.client.time.sleep", lambda _: None)
    with respx.mock(assert_all_called=True) as mock:
        add_successful_geocoding(mock)
        current = mock.get(WEATHER_URL).mock(
            side_effect=[httpx.Response(status_code) for _ in range(expected_calls)]
        )

        with pytest.raises(error_type):
            make_client().fetch_current("Recife", "BR")

    assert current.call_count == expected_calls


def test_fetch_current_retries_timeout_twice_then_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("app.adapters.outbound.openweather.client.time.sleep", lambda _: None)
    with respx.mock(assert_all_called=True) as mock:
        add_successful_geocoding(mock)
        current = mock.get(WEATHER_URL).mock(
            side_effect=[httpx.ReadTimeout("timeout") for _ in range(3)]
        )

        with pytest.raises(ProviderTimeout):
            make_client().fetch_current("Recife", "BR")

    assert current.call_count == 3


@pytest.mark.parametrize(
    "payload",
    [
        {
            "name": "Recife",
            "coord": {"lat": 91, "lon": 0},
            "main": {"temp": 20, "humidity": 50},
            "dt": 1,
        },
        {
            "name": "Recife",
            "coord": {"lat": 0, "lon": 181},
            "main": {"temp": 20, "humidity": 50},
            "dt": 1,
        },
        {"main": {"humidity": 50}, "dt": 1},
        {"main": {"temp": 20, "humidity": 101}, "dt": 1},
    ],
)
def test_fetch_current_rejects_invalid_weather_payload(payload: dict) -> None:
    with respx.mock(assert_all_called=True) as mock:
        add_successful_geocoding(mock)
        mock.get(WEATHER_URL).mock(return_value=httpx.Response(200, json=payload))

        with pytest.raises(ProviderInvalidResponse):
            make_client().fetch_current("Recife", "BR")
