from alembic.config import Config
from sqlalchemy import inspect

from alembic import command


def test_initial_migration_creates_weather_readings_schema(database_engine) -> None:
    inspector = inspect(database_engine)

    assert inspector.has_table("weather_readings")

    columns = {column["name"]: column for column in inspector.get_columns("weather_readings")}
    assert set(columns) == {
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
        "raw_payload",
    }

    unique_constraints = inspector.get_unique_constraints("weather_readings")
    assert any(
        constraint["column_names"] == ["city_name", "country_code", "source"]
        for constraint in unique_constraints
    )
    indexes = inspector.get_indexes("weather_readings")
    assert any(
        index["column_names"] == ["observed_at"] and "desc" in index["name"] for index in indexes
    )
    check_constraints = inspector.get_check_constraints("weather_readings")
    assert any(
        constraint["name"] == "ck_weather_readings_humidity_range"
        for constraint in check_constraints
    )


def test_initial_migration_downgrade_removes_its_table(database_engine) -> None:
    config = Config("alembic.ini")
    config.set_main_option(
        "sqlalchemy.url",
        database_engine.url.render_as_string(hide_password=False),
    )
    assert inspect(database_engine).has_table("weather_readings")

    command.downgrade(config, "base")
    assert not inspect(database_engine).has_table("weather_readings")
    command.upgrade(config, "head")
