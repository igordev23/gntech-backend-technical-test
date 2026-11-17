import time
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any
from uuid import uuid4

import httpx

from app.config import Settings
from app.domain.errors import (
    CityNotFound,
    ProviderAuthError,
    ProviderInvalidResponse,
    ProviderNotConfigured,
    ProviderRateLimited,
    ProviderTimeout,
    ProviderUnavailable,
)
from app.domain.models import WeatherReading

_RETRY_DELAYS_SECONDS = (0.5, 1.0)


class OpenWeatherClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def fetch_current(self, city: str, country: str | None) -> WeatherReading:
        city = city.strip()
        country = country.upper() if country else None
        api_key = self._get_api_key()
        location_query = f"{city},{country}" if country else city
        geocoding_payload = self._get_json(
            f"{self.settings.openweather_geocoding_base_url.rstrip('/')}/direct",
            {"q": location_query, "limit": 5, "appid": api_key},
        )
        location = self._select_location(geocoding_payload, city, country)

        current_payload = self._get_json(
            f"{self.settings.openweather_base_url.rstrip('/')}/weather",
            {
                "lat": location["lat"],
                "lon": location["lon"],
                "appid": api_key,
                "units": "metric",
                "lang": "pt_br",
            },
        )
        return self._to_reading(current_payload, location)

    def _get_api_key(self) -> str:
        configured_key = self.settings.openweather_api_key
        if configured_key is None:
            raise ProviderNotConfigured
        if hasattr(configured_key, "get_secret_value"):
            api_key = configured_key.get_secret_value()
        else:
            api_key = str(configured_key)
        if not api_key.strip():
            raise ProviderNotConfigured
        return api_key

    def _get_json(self, url: str, params: dict[str, object]) -> Any:
        retries = self.settings.openweather_max_retries
        timeout = self.settings.openweather_timeout_seconds

        for attempt in range(retries + 1):
            try:
                response = httpx.get(url, params=params, timeout=timeout)
            except httpx.TimeoutException as error:
                if attempt < retries:
                    time.sleep(_RETRY_DELAYS_SECONDS[attempt])
                    continue
                raise ProviderTimeout from error
            except httpx.RequestError as error:
                raise ProviderUnavailable from error

            if response.status_code == 429 or 500 <= response.status_code < 600:
                if attempt < retries:
                    time.sleep(_RETRY_DELAYS_SECONDS[attempt])
                    continue
            self._raise_for_status(response.status_code)

            try:
                return response.json()
            except (ValueError, UnicodeDecodeError) as error:
                raise ProviderInvalidResponse from error

        raise ProviderUnavailable

    @staticmethod
    def _raise_for_status(status_code: int) -> None:
        if status_code < 400:
            return
        if status_code == 401:
            raise ProviderAuthError
        if status_code == 429:
            raise ProviderRateLimited
        if 500 <= status_code < 600:
            raise ProviderUnavailable
        raise ProviderInvalidResponse

    @classmethod
    def _select_location(cls, payload: Any, city: str, country: str | None) -> dict[str, Any]:
        if not isinstance(payload, list):
            raise ProviderInvalidResponse
        locations = [cls._validate_location(item) for item in payload]
        if not locations:
            raise CityNotFound(city, country)
        if country:
            for location in locations:
                if location["country"] == country:
                    return location
            raise CityNotFound(city, country)
        return locations[0]

    @classmethod
    def _validate_location(cls, item: Any) -> dict[str, Any]:
        if not isinstance(item, dict):
            raise ProviderInvalidResponse
        name = item.get("name")
        country = item.get("country")
        if not isinstance(name, str) or not name.strip() or len(name) > 120:
            raise ProviderInvalidResponse
        if (
            not isinstance(country, str)
            or len(country) != 2
            or not country.isascii()
            or not country.isalpha()
        ):
            raise ProviderInvalidResponse
        latitude = cls._required_decimal(item.get("lat"))
        longitude = cls._required_decimal(item.get("lon"))
        cls._validate_coordinates(latitude, longitude)
        return {
            "name": name,
            "country": country.upper(),
            "lat": latitude,
            "lon": longitude,
        }

    @classmethod
    def _to_reading(cls, payload: Any, location: dict[str, Any]) -> WeatherReading:
        if not isinstance(payload, dict):
            raise ProviderInvalidResponse

        main = payload.get("main")
        if not isinstance(main, dict):
            raise ProviderInvalidResponse
        temperature = cls._required_decimal(main.get("temp"))
        humidity = main.get("humidity")
        if isinstance(humidity, bool) or not isinstance(humidity, int) or not 0 <= humidity <= 100:
            raise ProviderInvalidResponse

        coordinate_data = payload.get("coord", {})
        if coordinate_data is None:
            coordinate_data = {}
        if not isinstance(coordinate_data, dict):
            raise ProviderInvalidResponse
        latitude = (
            cls._required_decimal(coordinate_data["lat"])
            if "lat" in coordinate_data
            else location["lat"]
        )
        longitude = (
            cls._required_decimal(coordinate_data["lon"])
            if "lon" in coordinate_data
            else location["lon"]
        )
        cls._validate_coordinates(latitude, longitude)

        system = payload.get("sys", {})
        if system is None:
            system = {}
        if not isinstance(system, dict):
            raise ProviderInvalidResponse
        city_name = payload.get("name")
        if city_name is not None and not isinstance(city_name, str):
            raise ProviderInvalidResponse
        if city_name is not None and len(city_name) > 120:
            raise ProviderInvalidResponse
        if city_name is None or not city_name.strip():
            city_name = location["name"]
        country_code = system.get("country", location["country"])
        if (
            not isinstance(country_code, str)
            or len(country_code) != 2
            or not country_code.isascii()
            or not country_code.isalpha()
        ):
            raise ProviderInvalidResponse

        weather = payload.get("weather", [])
        if weather is None:
            weather = []
        if not isinstance(weather, list):
            raise ProviderInvalidResponse
        weather_item = weather[0] if weather else {}
        if not isinstance(weather_item, dict):
            raise ProviderInvalidResponse
        wind = payload.get("wind", {})
        if wind is None:
            wind = {}
        if not isinstance(wind, dict):
            raise ProviderInvalidResponse

        observed_at = payload.get("dt")
        if isinstance(observed_at, bool) or not isinstance(observed_at, int):
            raise ProviderInvalidResponse
        try:
            observed_datetime = datetime.fromtimestamp(observed_at, tz=UTC)
        except (OverflowError, OSError, ValueError) as error:
            raise ProviderInvalidResponse from error

        return WeatherReading(
            id=uuid4(),
            city_name=city_name.strip(),
            country_code=country_code.upper(),
            latitude=latitude,
            longitude=longitude,
            temperature_c=temperature,
            feels_like_c=cls._optional_decimal(main.get("feels_like")),
            humidity=humidity,
            pressure_hpa=cls._optional_int(main.get("pressure")),
            wind_speed_ms=cls._optional_decimal(wind.get("speed")),
            weather_main=cls._optional_string(weather_item.get("main"), 64),
            weather_description=cls._optional_string(weather_item.get("description"), 255),
            observed_at=observed_datetime,
            fetched_at=datetime.now(UTC),
            source="openweather",
            raw_payload=payload,
        )

    @classmethod
    def _required_decimal(cls, value: Any) -> Decimal:
        result = cls._optional_decimal(value)
        if result is None:
            raise ProviderInvalidResponse
        return result

    @staticmethod
    def _optional_decimal(value: Any) -> Decimal | None:
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, (int, float, Decimal)):
            raise ProviderInvalidResponse
        try:
            result = Decimal(str(value))
        except InvalidOperation as error:
            raise ProviderInvalidResponse from error
        if not result.is_finite():
            raise ProviderInvalidResponse
        return result

    @staticmethod
    def _optional_int(value: Any) -> int | None:
        if value is None:
            return None
        if isinstance(value, bool) or not isinstance(value, int):
            raise ProviderInvalidResponse
        return value

    @staticmethod
    def _optional_string(value: Any, max_length: int) -> str | None:
        if value is None:
            return None
        if not isinstance(value, str) or len(value) > max_length:
            raise ProviderInvalidResponse
        return value

    @staticmethod
    def _validate_coordinates(latitude: Decimal, longitude: Decimal) -> None:
        if not Decimal("-90") <= latitude <= Decimal("90"):
            raise ProviderInvalidResponse
        if not Decimal("-180") <= longitude <= Decimal("180"):
            raise ProviderInvalidResponse
