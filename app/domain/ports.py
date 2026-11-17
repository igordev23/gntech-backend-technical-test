from typing import Protocol
from uuid import UUID

from app.domain.models import WeatherReading


class WeatherProvider(Protocol):
    def fetch_current(self, city: str, country: str | None) -> WeatherReading: ...


class WeatherRepository(Protocol):
    def upsert(self, reading: WeatherReading) -> WeatherReading: ...

    def list_readings(
        self, city: str | None, country: str | None, page: int, page_size: int
    ) -> tuple[list[WeatherReading], int]: ...

    def get_by_id(self, reading_id: UUID) -> WeatherReading | None: ...

    def check_health(self) -> None: ...
