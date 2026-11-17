import os
from collections.abc import Iterator

import pytest
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

from alembic import command
from app.adapters.outbound.postgres.repository import PostgresWeatherRepository
from app.config import Settings, get_settings
from app.main import create_app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> Iterator[TestClient]:
    database_url = os.environ.get("TEST_DATABASE_URL") or Settings().test_database_url
    monkeypatch.setenv("DATABASE_URL", database_url)
    monkeypatch.setenv("OPENWEATHER_API_KEY", "test-key")
    get_settings.cache_clear()
    with TestClient(create_app()) as test_client:
        yield test_client
    get_settings.cache_clear()


@pytest.fixture(scope="session")
def database_engine() -> Iterator[Engine]:
    database_url = os.environ.get("TEST_DATABASE_URL") or Settings().test_database_url
    engine = create_engine(database_url)

    alembic_config = Config("alembic.ini")
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")

    yield engine

    engine.dispose()


@pytest.fixture
def clear_weather_readings(database_engine: Engine) -> None:
    if inspect(database_engine).has_table("weather_readings"):
        with database_engine.begin() as connection:
            connection.execute(text("TRUNCATE TABLE weather_readings"))


@pytest.fixture
def repository(database_engine: Engine) -> PostgresWeatherRepository:
    session_factory = sessionmaker(bind=database_engine, expire_on_commit=False)
    return PostgresWeatherRepository(session_factory)
