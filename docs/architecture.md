# Arquitetura

## Stack

- Python 3.12
- FastAPI + Pydantic v2
- SQLAlchemy 2.0 (sync) + Alembic
- PostgreSQL 16
- httpx (cliente OpenWeather)
- uv (dependências e lockfile)
- pytest + respx (testes)
- Ruff (lint/format)
- Docker + Docker Compose

## Processes

### Sync

1. `POST /api/v1/weather/sync` valida `city`/`country` no schema Pydantic.
2. O service monta a chamada e o client httpx consulta a OpenWeather com `q`, `appid`, `units=metric` e `lang=pt_br`.
3. O client aplica timeout, retries limitados e traduz erros HTTP/rede para erros de domínio.
4. A resposta é validada por um schema Pydantic antes de entrar no domínio.
5. O repository faz `INSERT ... ON CONFLICT (city_name, country_code, source) DO UPDATE`.
6. A rota devolve a leitura persistida.

### Consulta

1. `GET /api/v1/weather` valida filtros e paginação.
2. O service monta a query.
3. O repository executa count + select ordenado por `observed_at DESC`.
4. A rota devolve `items`, `total`, `page` e `page_size`.

### Health

`GET /health` executa `SELECT 1` no banco; retorna 200 ou 503.

## Packages

### Runtime

`fastapi`, `uvicorn[standard]`, `sqlalchemy`, `psycopg[binary]`, `alembic`, `pydantic-settings`, `httpx`.

### Desenvolvimento

`pytest`, `respx`, `ruff`.

> Nenhum pacote foi instalado na etapa de fundação.

## Module shapes

```text
app/
├── main.py                 # app factory, routers, exception handlers
├── core/
│   ├── config.py           # pydantic-settings
│   ├── errors.py           # erros de domínio + handlers
│   └── logging.py          # logging sem segredos
├── api/
│   ├── deps.py             # dependências (sessão, service, client)
│   └── routes/
│       ├── health.py
│       └── weather.py
├── services/
│   └── weather.py          # regras de sync e consulta
├── clients/
│   └── openweather.py      # httpx, timeout, retry, tradução de erros
├── repositories/
│   └── weather.py          # queries e upsert
├── models/
│   └── weather.py          # tabela weather_readings
├── schemas/
│   └── weather.py          # contratos Pydantic
└── db/
    ├── base.py             # Base declarativa
    └── session.py          # engine e session
alembic/
└── versions/
scripts/
└── seed.py                 # dados de exemplo (sem chamar a API real)
tests/
├── unit/
└── integration/
```

### Regras de camadas

- Rotas não acessam o banco diretamente.
- Services não conhecem HTTP nem SQLAlchemy; orquestram client + repository.
- Client não conhece banco; repository não conhece HTTP.
- Schemas Pydantic são o contrato de entrada/saída; modelos ORM não vazam para a API.
- Erros de infraestrutura são traduzidos para erros de domínio em `core/errors.py`.

## Data

Banco: PostgreSQL 16. Uma tabela.

### `weather_readings`

| Coluna | Tipo | Regra |
|---|---|---|
| `id` | `UUID` | PK, `gen_random_uuid()` |
| `city_name` | `VARCHAR(120)` | obrigatório |
| `country_code` | `CHAR(2)` | obrigatório |
| `latitude` | `NUMERIC(9,6)` | opcional |
| `longitude` | `NUMERIC(9,6)` | opcional |
| `temperature_c` | `NUMERIC(5,2)` | obrigatório |
| `feels_like_c` | `NUMERIC(5,2)` | opcional |
| `humidity` | `SMALLINT` | `CHECK (humidity BETWEEN 0 AND 100)` |
| `pressure_hpa` | `INTEGER` | opcional |
| `wind_speed_ms` | `NUMERIC(5,2)` | opcional |
| `weather_main` | `VARCHAR(64)` | opcional |
| `weather_description` | `VARCHAR(255)` | opcional |
| `observed_at` | `TIMESTAMPTZ` | obrigatório, UTC |
| `fetched_at` | `TIMESTAMPTZ` | `NOT NULL DEFAULT now()`, UTC |
| `source` | `VARCHAR(32)` | `NOT NULL DEFAULT 'openweather'` |
| `raw_payload` | `JSONB` | opcional, auditoria |

Constraints e índices:

- `UNIQUE (city_name, country_code, source)` — garante uma linha por cidade/país/provedor.
- `INDEX (observed_at DESC)` — ordenação da listagem.
- `CHECK (humidity BETWEEN 0 AND 100)`.

O `country_code` vem de `sys.country` da resposta. Se o provedor não retornar, usa o país informado na requisição; sem nenhum dos dois, a resposta é tratada como inválida.

### Segredos

- `OPENWEATHER_API_KEY` e credenciais do Postgres vêm de variáveis de ambiente.
- `.env` é gitignored; `.env.example` não contém valores reais.
- Logs nunca incluem a URL completa da OpenWeather (a key vai na query string).

## Docker

- `docker compose up --build` sobe `api` e `db`.
- `db`: PostgreSQL 16 com volume nomeado e healthcheck.
- `api`: build local, healthcheck em `/health`, depende do `db` saudável.
- O entrypoint aplica `alembic upgrade head` antes de subir o Uvicorn.
- Seed: `docker compose run --rm api python scripts/seed.py`.
- Execução local apenas; sem deploy público nesta entrega.

## Idioma

- Documentação e planos: português.
- Código, testes, identificadores, comentários, docstrings, logs e mensagens de commit: 100% inglês.

## Git flow

`main` estável, `develop` de integração, `feat/*` por plano, `release/*` para entrega. Detalhes em `docs/git-flow.md`.
