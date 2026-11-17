FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:0.12.19 /uv /uvx /bin/

WORKDIR /app

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    PYTHONPATH=/app

COPY pyproject.toml uv.lock alembic.ini ./
RUN uv sync --frozen --no-dev

COPY app ./app
COPY alembic ./alembic
COPY scripts/seed.py ./scripts/seed.py

CMD ["sh", "-c", "uv run --no-sync alembic -x database_url=\"$DATABASE_URL\" upgrade head && exec uv run --no-sync uvicorn app.main:app --host 0.0.0.0 --port 8000"]
