# Getting started

> A API e o ambiente local são definidos pelo plano `plans/002-weather-api.md`.

## Pré-requisitos

- Docker 24+ e Docker Compose v2
- Uma API key gratuita da OpenWeather (Current Weather)
- Opcional para desenvolvimento local: Python 3.12 + uv

## Setup

1. Copie o arquivo de exemplo:

   ```bash
   cp -n .env.example .env
   ```

2. Preencha `OPENWEATHER_API_KEY` no `.env`.

3. Suba o ambiente:

   ```bash
   docker compose up --build
   ```

4. Abra o Swagger em http://localhost:8000/docs.

O `docker compose` aplica as migrations automaticamente antes de subir a API.

## Variáveis de ambiente

| Variável | Obrigatória | Padrão | Finalidade |
|---|---|---|---|
| `POSTGRES_USER` | não | `weather` | usuário do PostgreSQL local |
| `POSTGRES_PASSWORD` | não | `weather` | senha local; nunca use em produção |
| `POSTGRES_DB` | não | `weather` | banco da aplicação |
| `POSTGRES_PORT` | não | `5432` | porta do Postgres no host |
| `DATABASE_URL` | não | `postgresql+psycopg://weather:weather@localhost:5432/weather` | conexão fora do Docker; o compose sobrescreve com host `db` |
| `TEST_DATABASE_URL` | não | `postgresql+psycopg://weather:weather@localhost:5432/weather_test` | banco usado pelos testes de integração |
| `OPENWEATHER_API_KEY` | sim, para sync | — | chave da OpenWeather; nunca commitar |
| `OPENWEATHER_GEOCODING_BASE_URL` | não | `https://api.openweathermap.org/geo/1.0` | base do Geocoding API usado antes da consulta |
| `OPENWEATHER_BASE_URL` | não | `https://api.openweathermap.org/data/2.5` | base da API externa |
| `OPENWEATHER_TIMEOUT_SECONDS` | não | `5` | timeout por requisição |
| `OPENWEATHER_MAX_RETRIES` | não | `2` | tentativas extras por chamada HTTP em timeout/429/5xx |
| `API_PORT` | não | `8000` | porta da API no host |
| `APP_ENV` | não | `development` | ambiente lógico (`development`, `test`, `production`) |
| `LOG_LEVEL` | não | `INFO` | nível de log |

## Seed

Para testar os GETs sem uma API key:

```bash
docker compose run --rm api python scripts/seed.py
```

## Testes

Inicie o PostgreSQL e prepare um banco separado para os testes:

```bash
docker compose up -d db
docker compose exec -T db createdb -U weather weather_test
uv sync --frozen
TEST_DATABASE_URL=postgresql+psycopg://weather:weather@localhost:5432/weather_test uv run pytest
```

## Migrations

Automáticas no `docker compose up --build` antes do Uvicorn iniciar.

## Notas

- `.env` é gitignored; nunca commite.
- O ambiente Docker é local. Não há deploy público nesta entrega.
- Se a porta 5432 já estiver em uso, ajuste `POSTGRES_PORT`.
- Sem `OPENWEATHER_API_KEY`, a API sobe e os GETs funcionam com seed; o sync retorna 503.
