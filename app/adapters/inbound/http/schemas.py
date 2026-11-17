from datetime import UTC, datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class WeatherSyncRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    city: str = Field(min_length=1, max_length=120)
    country: str | None = Field(default=None, pattern=r"^[A-Za-z]{2}$")


class WeatherListQuery(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    city: str | None = Field(default=None, min_length=1, max_length=120)
    country: str | None = Field(default=None, pattern=r"^[A-Za-z]{2}$")
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class WeatherReadingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

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

    @field_serializer(
        "latitude",
        "longitude",
        "temperature_c",
        "feels_like_c",
        "wind_speed_ms",
    )
    def serialize_decimal(self, value: Decimal | None) -> float | None:
        return float(value) if value is not None else None

    @field_serializer("observed_at", "fetched_at")
    def serialize_utc_datetime(self, value: datetime) -> str:
        return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


class WeatherListResponse(BaseModel):
    items: list[WeatherReadingResponse]
    total: int
    page: int
    page_size: int


class HealthResponse(BaseModel):
    status: str
    database: str
