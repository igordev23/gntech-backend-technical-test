from collections.abc import Callable
from uuid import UUID

from sqlalchemy import func, select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.adapters.outbound.postgres.models import WeatherReadingModel
from app.domain.errors import DatabaseUnavailable
from app.domain.models import WeatherReading


class PostgresWeatherRepository:
    def __init__(self, session_factory: Callable[[], Session]) -> None:
        self.session_factory = session_factory

    def upsert(self, reading: WeatherReading) -> WeatherReading:
        values = {
            "id": reading.id,
            "city_name": reading.city_name,
            "country_code": reading.country_code,
            "latitude": reading.latitude,
            "longitude": reading.longitude,
            "temperature_c": reading.temperature_c,
            "feels_like_c": reading.feels_like_c,
            "humidity": reading.humidity,
            "pressure_hpa": reading.pressure_hpa,
            "wind_speed_ms": reading.wind_speed_ms,
            "weather_main": reading.weather_main,
            "weather_description": reading.weather_description,
            "observed_at": reading.observed_at,
            "fetched_at": reading.fetched_at,
            "source": reading.source,
            "raw_payload": reading.raw_payload,
        }
        statement = insert(WeatherReadingModel).values(**values)
        statement = statement.on_conflict_do_update(
            index_elements=[
                WeatherReadingModel.city_name,
                WeatherReadingModel.country_code,
                WeatherReadingModel.source,
            ],
            set_={
                column: getattr(statement.excluded, column)
                for column in values
                if column not in {"id", "city_name", "country_code", "source"}
            },
        ).returning(WeatherReadingModel)
        try:
            with self.session_factory() as session, session.begin():
                persisted = session.scalar(statement)
                if persisted is None:
                    raise DatabaseUnavailable
                return self._to_domain(persisted)
        except SQLAlchemyError as error:
            raise DatabaseUnavailable from error

    def list_readings(
        self, city: str | None, country: str | None, page: int, page_size: int
    ) -> tuple[list[WeatherReading], int]:
        filters = []
        if city:
            filters.append(func.lower(WeatherReadingModel.city_name) == city.lower())
        if country:
            filters.append(WeatherReadingModel.country_code == country.upper())
        try:
            with self.session_factory() as session:
                total = session.scalar(
                    select(func.count()).select_from(WeatherReadingModel).where(*filters)
                )
                statement = (
                    select(WeatherReadingModel)
                    .where(*filters)
                    .order_by(WeatherReadingModel.observed_at.desc())
                    .offset((page - 1) * page_size)
                    .limit(page_size)
                )
                rows = session.scalars(statement).all()
                return [self._to_domain(row) for row in rows], total or 0
        except SQLAlchemyError as error:
            raise DatabaseUnavailable from error

    def get_by_id(self, reading_id: UUID) -> WeatherReading | None:
        try:
            with self.session_factory() as session:
                row = session.get(WeatherReadingModel, reading_id)
                return self._to_domain(row) if row is not None else None
        except SQLAlchemyError as error:
            raise DatabaseUnavailable from error

    def check_health(self) -> None:
        try:
            with self.session_factory() as session:
                session.execute(text("SELECT 1"))
        except SQLAlchemyError as error:
            raise DatabaseUnavailable from error

    @staticmethod
    def _to_domain(row: WeatherReadingModel) -> WeatherReading:
        return WeatherReading(
            id=row.id,
            city_name=row.city_name,
            country_code=row.country_code,
            latitude=row.latitude,
            longitude=row.longitude,
            temperature_c=row.temperature_c,
            feels_like_c=row.feels_like_c,
            humidity=row.humidity,
            pressure_hpa=row.pressure_hpa,
            wind_speed_ms=row.wind_speed_ms,
            weather_main=row.weather_main,
            weather_description=row.weather_description,
            observed_at=row.observed_at,
            fetched_at=row.fetched_at,
            source=row.source,
            raw_payload=row.raw_payload,
        )
