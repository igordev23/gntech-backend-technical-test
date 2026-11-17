from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from uuid import UUID


@dataclass
class WeatherReading:
    id: UUID
    city_name: str
    country_code: str
    latitude: Decimal | None
    longitude: Decimal | None
    temperature_c: Decimal
    feels_like_c: Decimal | None
    humidity: int
    pressure_hpa: int | None
    wind_speed_ms: Decimal | None
    weather_main: str | None
    weather_description: str | None
    observed_at: datetime
    fetched_at: datetime
    source: str
    raw_payload: dict[str, object] | None
