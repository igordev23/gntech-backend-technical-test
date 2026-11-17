# 002 — API de clima

## Origem

Pedido para implementar o contrato definido em `docs/PROJECT.md`: sincronização com a OpenWeather, persistência no PostgreSQL, consulta por HTTP e execução local com Docker Compose.

Este plano começa após a fundação já mesclada em `develop`. Nenhuma implementação deve existir antes da aprovação e do merge deste plano.

## Contrato alvo

### Stack e estrutura

- Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 sync, Alembic, PostgreSQL 16, httpx e uv.
- Arquitetura Hexagonal com as duas portas já registradas em D-002:
  - `WeatherProvider`;
  - `WeatherRepository`.
- Adaptadores de entrada em `app/adapters/inbound/http/`.
- Adaptadores de saída em `app/adapters/outbound/openweather/` e `app/adapters/outbound/postgres/`.
- O núcleo em `app/domain/` e `app/application/` não importa FastAPI, SQLAlchemy, httpx ou Pydantic.

### Endpoints

#### `POST /api/v1/weather/sync`

- Entrada JSON: `city` obrigatório, com tamanho de 1 a 120 caracteres; `country` opcional no formato ISO 3166-1 alpha-2.
- Normaliza `country` para maiúsculas.
- Consulta a OpenWeather com `q=<city>,<country>` ou `q=<city>`, `appid`, `units=metric` e `lang=pt_br`.
- Faz upsert de uma única leitura por `(city_name, country_code, source)`.
- Retorna `200` com o recurso persistido.

#### `GET /api/v1/weather`

- Filtros opcionais: `city`, `country`.
- Paginação: `page` inteiro mínimo 1, padrão 1; `page_size` inteiro entre 1 e 100, padrão 20.
- Ordenação fixa: `observed_at DESC`.
- Resposta: `{ "items": [...], "total": <int>, "page": <int>, "page_size": <int> }`.

#### `GET /api/v1/weather/{id}`

- `id` é UUID.
- Retorna `200` com a leitura correspondente.
- Retorna `404` com `reading_not_found` quando não existe.

#### `GET /health`

- Executa uma consulta mínima no banco.
- Retorna `200` com estado de API e banco quando íntegro.
- Retorna `503` com `database_unavailable` quando o banco não responde.

#### Documentação

- Swagger em `/docs` e OpenAPI em `/openapi.json`.

### Contrato de dados

A entidade de domínio `WeatherReading` contém: `id`, `city_name`, `country_code`, `latitude`, `longitude`, `temperature_c`, `feels_like_c`, `humidity`, `pressure_hpa`, `wind_speed_ms`, `weather_main`, `weather_description`, `observed_at`, `fetched_at`, `source` e `raw_payload`.

A migration cria `weather_readings` conforme `docs/architecture.md`, incluindo:

- chave primária UUID;
- `UNIQUE (city_name, country_code, source)`;
- índice em `observed_at DESC`;
- `CHECK (humidity BETWEEN 0 AND 100)`;
- timestamps UTC;
- `raw_payload` como JSONB.

### Erros

Toda resposta de domínio ou infraestrutura usa `{ "error": "codigo_snake", "details": { ... } }`. Erros de validação do Pydantic usam o mesmo envelope.

| Situação | Status | Código |
|---|---:|---|
| Payload ou parâmetro inválido | 422 | `validation_error` |
| Cidade não encontrada pelo provedor | 404 | `city_not_found` |
| API key ausente | 503 | `provider_not_configured` |
| API key rejeitada pelo provedor | 503 | `provider_auth_error` |
| Limite de requisições excedido | 429 | `provider_rate_limited` |
| Timeout da OpenWeather | 504 | `provider_timeout` |
| Resposta inválida da OpenWeather | 502 | `provider_invalid_response` |
| Falha 5xx da OpenWeather | 502 | `provider_unavailable` |
| Leitura não encontrada | 404 | `reading_not_found` |
| Banco indisponível | 503 | `database_unavailable` |

O código interno nunca vaza chave, URL completa ou payload sensível.

### Seed

O script `scripts/seed.py` grava exemplos diretamente no PostgreSQL, sem chamar a OpenWeather.

- Usa `source="openweather"` para respeitar a chave única existente.
- Realiza upsert pelas mesmas chaves usadas pelo sync.
- Permite repetir o comando sem duplicar cidades.
- Popula dados de São Paulo, Rio de Janeiro e outra cidade exemplo.

## Decisões

- D-002: arquitetura Hexagonal enxuta com duas portas.
- D-004: persistência da última leitura por cidade, país e provedor.
- D-006: httpx como client da OpenWeather.
- D-009: envelope único de erros.
- D-011: seed local sem chamada externa.
- D-012: testes por camada.

Decisões fechadas especificamente por este plano:

- **D-016 — estratégia do seed:** o seed usa `source="openweather"` e upsert pela mesma chave do sync.
- **D-017 — catálogo de erros:** os códigos e status da tabela acima.
- **D-018 — paginação:** `page=1`, `page_size=20`, máximo 100 e ordenação por `observed_at DESC`.
- **D-019 — retry do provedor:** timeout de 5 segundos, até 2 tentativas adicionais, com backoff limitado; retry em 429 e respostas 5xx; sem retry em 401 e 404.
- **D-020 — payload bruto:** `raw_payload` é gravado em JSONB por padrão e nunca é usado como fonte de verdade.

## Fora de escopo

- Histórico temporal de leituras.
- Autenticação ou autorização.
- Agendamento, filas, cache e múltiplos provedores.
- Deploy público.
- Frontend.
- Telemetria além dos logs básicos.
- Chamadas reais à OpenWeather no CI.

## RED → GREEN → REFACTOR

As specs devem falhar pela ausência do comportamento, não por falha de ambiente ou importação.

### RED 1 — domínio e serviço

- Arquivos: `tests/unit/test_weather_service.py`, `tests/unit/test_models.py`.
- Cenários: upsert por sync, listagem paginada, consulta por ID inexistente e mapear cidade ausente.
- Falha esperada: módulos ou contratos ainda não existem.
- Comando: `uv run pytest tests/unit/test_weather_service.py tests/unit/test_models.py`.

### GREEN 1

Criar `app/domain/models.py`, `app/domain/ports.py`, `app/domain/errors.py` e `app/application/weather_service.py`, com fakes nas portas.

### RED 2 — client OpenWeather

- Arquivo: `tests/unit/test_openweather_client.py`.
- Cenários: 404, 401, 429, timeout, 5xx, payload inválido e ausência de API key.
- Testar toda chamada sem rede usando `respx`.
- Comando: `uv run pytest tests/unit/test_openweather_client.py`.

### GREEN 2

Criar `app/adapters/outbound/openweather/client.py` e `app/config.py`, respeitando timeout e retry definidos em D-019.

### RED 3 — migration e repository

- Arquivos: `tests/integration/test_weather_repository.py`, `tests/integration/test_migration.py`.
- Cenários: upsert idempotente, filtros, paginação, consulta por ID e constraints.
- Banco: `TEST_DATABASE_URL`, migrations aplicadas antes da suite.
- Comando: `uv run pytest tests/integration/test_weather_repository.py tests/integration/test_migration.py`.

### GREEN 3

Criar a migration inicial, `app/adapters/outbound/postgres/models.py`, `session.py` e `repository.py`.

### RED 4 — API e Docker

- Arquivos: `tests/integration/test_weather_api.py`, `tests/integration/test_health_api.py`.
- Cenários: sync com provider fake, listagem, consulta por ID, 404, health saudável e health sem banco.
- Comando: `uv run pytest tests/integration/test_weather_api.py tests/integration/test_health_api.py`.

### GREEN 4

Criar a aplicação FastAPI, schemas Pydantic, rotas, composition root, handlers de erro e configuração Docker Compose.

### RED 5 — seed

- Arquivo: `tests/integration/test_seed.py`.
- Cenário: executar o seed duas vezes não duplica leitura.
- Comando: `uv run pytest tests/integration/test_seed.py`.

### GREEN 5

Criar `scripts/seed.py` e documentar o comando de execução.

### REFACTOR

Após todas as specs focadas ficarem verdes:

- remover duplicação de mapeamento entre domínio, ORM e schemas;
- manter Pydantic, SQLAlchemy e httpx fora do núcleo;
- revisar logs e garantia de que segredos não vazam;
- executar Ruff e toda a suite.

## Riscos

- A OpenWeather pode mudar ou omitir campos; o adaptador valida o contrato mínimo e rejeita payload inválido.
- Valores numéricos de temperatura e coordenadas podem exigir limites ou precisão; migration usa `NUMERIC` e o domínio mantém precisão no banco.
- Retry excessivo pode ampliar timeout em picos; D-019 limita as tentativas e usa backoff curto.
- Dados de seed podem parecer dados reais; logs e documentação devem identificá-los como exemplos.
- Banco indisponível na inicialização deve falhar de forma explícita; o entrypoint aplica migration antes do Uvicorn.

## Configuração e infraestrutura

Arquivos alvo da implementação:

- `pyproject.toml`, `uv.lock`;
- `app/` e a estrutura descrita em `docs/architecture.md`;
- `alembic.ini`, `alembic/`;
- `Dockerfile`, `docker-compose.yml`;
- `.env.example` já existente;
- `scripts/seed.py`;
- `tests/`;
- `.github/workflows/ci.yml`;
- documentação afetada em `README.md` e `docs/getting-started.md`.

O `.repo-model.json` muda de `status: "template"` para `status: "active"` e recebe o `validation_command` somente no PR de implementação, depois que o comando real existir.

## Critério de pronto

- [ ] Plano mergeado em `develop` antes da implementação.
- [ ] Todas as specs RED falharam pela ausência do comportamento correto.
- [ ] Todas as specs GREEN e a suite ampla passam.
- [ ] O nucleus não importa FastAPI, SQLAlchemy, httpx ou Pydantic.
- [ ] A migration é reproduzível em banco vazio e aplica upsert idempotente.
- [ ] Testes não chamam a OpenWeather real.
- [ ] Docker Compose sobe API + PostgreSQL e aplica migrations.
- [ ] Seed funciona sem chave da OpenWeather.
- [ ] Swagger, erros, README e docs de execução refletem o contrato.
- [ ] `.repo-model.json` passa para `active` com comando de validação real.
- [ ] Ruff check e Ruff format passam.
- [ ] Nenhum segredo foi incluído no Git.
