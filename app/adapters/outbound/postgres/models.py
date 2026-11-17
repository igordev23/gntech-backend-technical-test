from datetime import datetime
from decimal import Decimal
from uuid import UUID as PythonUUID

from sqlalchemy import (
    CHAR,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    Numeric,
    SmallInteger,
    String,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class WeatherReadingModel(Base):
    __tablename__ = "weather_readings"
    __table_args__ = (
        UniqueConstraint(
            "city_name",
            "country_code",
            "source",
            name="uq_weather_readings_city_country_source",
        ),
        CheckConstraint(
            "humidity BETWEEN 0 AND 100",
            name="ck_weather_readings_humidity_range",
        ),
        Index(
            "ix_weather_readings_observed_at_desc",
            text("observed_at DESC"),
        ),
    )

    id: Mapped[PythonUUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )
    city_name: Mapped[str] = mapped_column(String(120), nullable=False)
    country_code: Mapped[str] = mapped_column(CHAR(2), nullable=False)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(9, 6))
    temperature_c: Mapped[Decimal] = mapped_column(Numeric(5, 2), nullable=False)
    feels_like_c: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    humidity: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    pressure_hpa: Mapped[int | None] = mapped_column(Integer)
    wind_speed_ms: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    weather_main: Mapped[str | None] = mapped_column(String(64))
    weather_description: Mapped[str | None] = mapped_column(String(255))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
    )
    source: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        server_default=text("'openweather'"),
    )
    raw_payload: Mapped[dict | None] = mapped_column(JSONB)
