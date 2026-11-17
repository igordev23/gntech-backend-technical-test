import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "0001_create_weather_readings"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "weather_readings",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("city_name", sa.String(length=120), nullable=False),
        sa.Column("country_code", sa.CHAR(length=2), nullable=False),
        sa.Column("latitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("longitude", sa.Numeric(precision=9, scale=6), nullable=True),
        sa.Column("temperature_c", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("feels_like_c", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("humidity", sa.SmallInteger(), nullable=False),
        sa.Column("pressure_hpa", sa.Integer(), nullable=True),
        sa.Column("wind_speed_ms", sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column("weather_main", sa.String(length=64), nullable=True),
        sa.Column("weather_description", sa.String(length=255), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "fetched_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "source",
            sa.String(length=32),
            server_default=sa.text("'openweather'"),
            nullable=False,
        ),
        sa.Column("raw_payload", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.CheckConstraint(
            "humidity BETWEEN 0 AND 100",
            name="ck_weather_readings_humidity_range",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "city_name",
            "country_code",
            "source",
            name="uq_weather_readings_city_country_source",
        ),
    )
    op.create_index(
        "ix_weather_readings_observed_at_desc",
        "weather_readings",
        [sa.text("observed_at DESC")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_table("weather_readings")
