# Arquitetura

## Decisão: Hexagonal (Ports & Adapters)

A aplicação usa **Hexagonal Architecture** em versão enxuta, com duas portas. O objetivo é isolar a regra de negócio de FastAPI, SQLAlchemy e httpx sem criar a cerimônia de uma Clean Architecture completa.

### Por que Hexagonal neste projeto

- O problema tem dois sistemas externos simétricos: OpenWeather (fonte de dados) e PostgreSQL (persistência). Hexagonal trata os dois como adaptadores.
- O FastAPI é um adaptador de entrada; `Depends` é o composition root natural para montar o serviço com os adaptadores.
- O núcleo (`domain/` + `application/`) pode ser testado com fakes, sem subir HTTP ou banco.
- Trocar OpenWeather por outro provedor, ou PostgreSQL por outro banco, não exige mudar a regra de negócio.
- É proporcional: duas portas, nenhum unit of work, domain event, CQRS ou interface genérica.

### Frase para a entrevista

> “Escolhi Hexagonal porque o FastAPI é um adaptador de entrada e o `Depends` é o composition root natural. O núcleo não depende de FastAPI, SQLAlchemy ou httpx; OpenWeather e PostgreSQL entram atrás de duas portas. Isso deixa a regra de negócio testável com fakes e permite trocar provedor ou banco sem tocar no serviço. Não usei Clean Architecture completa porque o domínio tem uma entidade e quatro endpoints — seria cerimônia sem retorno.”

### Alternativas rejeitadas

> Resumo. O registro canônico, com contexto, consequências e status, é `docs/decisions.md` (D-002).

| Arquitetura | Por que não |
|---|---|
| Clean Architecture completa | Entidades + use cases + presenters + boundaries para 1 entidade e 4 endpoints vira cerimônia sem retorno. Hexagonal entrega a mesma inversão com menos conceitos. |
| Vertical Slice | Boa para muitas features; aqui existe basicamente uma feature (clima). As fronteiras de infraestrutura ficariam menos explícitas. |
| Camadas tradicionais | Genérica; não explica por que FastAPI está ali nem como trocar OpenWeather/Postgres sem tocar na regra. |
| MVC | FastAPI não é MVC; não há controller/view no sentido clássico. |
| DDD tático | O domínio é anêmico (uma leitura de clima). Aggregate/domain events não se pagam. |

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

1. `POST /api/v1/weather/sync` valida `city`/`country` no schema Pydantic (adaptador HTTP).
2. O `WeatherService` chama `WeatherProvider.fetch_current(city, country)`.
3. O adaptador OpenWeather consulta a API com `q`, `appid`, `units=metric` e `lang=pt_br`, aplica timeout/retries e valida a resposta.
4. O service recebe um `WeatherReading` e chama `WeatherRepository.upsert(reading)`.
5. O adaptador PostgreSQL executa `INSERT ... ON CONFLICT (city_name, country_code, source) DO UPDATE`.
6. A rota devolve o schema Pydantic da leitura persistida.

O service não sabe que existe FastAPI, httpx ou SQLAlchemy.

### Consulta

1. `GET /api/v1/weather` valida filtros e paginação no adaptador HTTP.
2. O `WeatherService` chama `WeatherRepository.list(...)`.
3. O adaptador PostgreSQL executa count + select ordenado por `observed_at DESC`.
4. A rota devolve `items`, `total`, `page` e `page_size`.

### Health

`GET /health` chama um check de banco no adaptador de persistência; retorna 200 ou 503.

## Packages

### Runtime

`fastapi`, `uvicorn[standard]`, `sqlalchemy`, `psycopg[binary]`, `alembic`, `pydantic-settings`, `httpx`.

### Desenvolvimento

`pytest`, `respx`, `ruff`.

> Nenhum pacote foi instalado na etapa de fundação.

## Module shapes

```text
app/
├── domain/
│   ├── models.py          # WeatherReading (dataclass)
│   ├── ports.py           # WeatherProvider, WeatherRepository (Protocols)
│   └── errors.py          # CityNotFound, UpstreamError, ...
├── application/
│   └── weather_service.py # sync_weather, list_readings, get_reading
├── adapters/
│   ├── inbound/
│   │   └── http/
│   │       ├── routes/weather.py
│   │       ├── routes/health.py
│   │       ├── schemas.py          # Pydantic (contrato HTTP)
│   │       ├── dependencies.py     # composition root com Depends
│   │       └── error_handlers.py   # domínio -> HTTP status
│   └── outbound/
│       ├── openweather/client.py   # implementa WeatherProvider
│       └── postgres/
│           ├── models.py           # ORM
│           ├── repository.py       # implementa WeatherRepository
│           └── session.py
├── config.py
└── main.py
alembic/
└── versions/
scripts/
└── seed.py                         # dados de exemplo (sem chamar a API real)
tests/
├── unit/
└── integration/
```

### Regra de dependência

- `domain/` importa apenas a biblioteca padrão e `typing`. Não importa FastAPI, SQLAlchemy, httpx nem Pydantic.
- `application/` importa `domain/`. Não importa framework nem infraestrutura.
- `adapters/` importam `domain/` e `application/` e podem importar as bibliotecas de infraestrutura.
- `main.py` e `dependencies.py` são o composition root: montam os adaptadores e injetam no service.
- Nenhum adaptador é importado pelo núcleo.
- Pydantic existe só na borda HTTP (schemas); o domínio usa dataclass.
- SQLAlchemy existe só em `adapters/outbound/postgres`.
- httpx existe só em `adapters/outbound/openweather`.

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

- Conteúdo de documentação e planos: português.
- Nomes de arquivos e pastas, código, testes, identificadores, comentários, docstrings, logs e mensagens de commit: 100% inglês.

## Git flow

`main` estável, `develop` de integração, `feat/*` por plano, `release/*` para entrega. Detalhes em `docs/git-flow.md`.
