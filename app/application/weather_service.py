from uuid import UUID

from app.domain.errors import ReadingNotFound
from app.domain.models import WeatherReading
from app.domain.ports import WeatherProvider, WeatherRepository


class WeatherService:
    def __init__(self, provider: WeatherProvider, repository: WeatherRepository) -> None:
        self.provider = provider
        self.repository = repository

    def sync_weather(self, city: str, country: str | None) -> WeatherReading:
        normalized_city = city.strip()
        normalized_country = country.upper() if country else None
        reading = self.provider.fetch_current(normalized_city, normalized_country)
        return self.repository.upsert(reading)

    def list_readings(
        self, city: str | None, country: str | None, page: int, page_size: int
    ) -> tuple[list[WeatherReading], int]:
        normalized_city = city.strip() if city else None
        normalized_country = country.upper() if country else None
        return self.repository.list_readings(normalized_city, normalized_country, page, page_size)

    def get_reading(self, reading_id: UUID) -> WeatherReading:
        reading = self.repository.get_by_id(reading_id)
        if reading is None:
            raise ReadingNotFound(reading_id)
        return reading
