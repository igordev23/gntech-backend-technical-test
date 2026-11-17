# 002 — API de clima

## Origem

Pedido para implementar o contrato definido em `docs/PROJECT.md`: sincronização com a OpenWeather, persistência no PostgreSQL, consulta por HTTP e execução local com Docker Compose.

Este plano começa após a fundação já mesclada em `develop`. Nenhuma implementação deve existir antes da aprovação e do merge deste plano.

## Documentos de referência obrigatória

Antes de implementar, consultar estes caminhos no branch de implementação:

1. `AGENTS.md` — limites de escopo, arquitetura obrigatória, idioma, comandos permitidos e regra de PR do plano antes do código.
2. `docs/PROJECT.md` — contrato de produto autoritativo: endpoints públicos, regras de negócio e itens fora de escopo. Se este plano divergir dele, parar e corrigir o plano antes de codificar.
3. `docs/architecture.md` — estrutura de módulos, direção das dependências, campos da tabela e fluxos esperados. Os caminhos abaixo concretizam esta estrutura, não a substituem.
4. `docs/decisions.md` — justificativas e decisões aceitas D-001 a D-022. Não substituir decisão sem emenda explícita.
5. `docs/testing.md` e `docs/sdd.md` — camadas de teste, uso de PostgreSQL/respx e sequência RED → GREEN.
6. `docs/getting-started.md` e `.env.example` — nomes de variáveis, comandos locais e configuração alvo.
7. `docs/git-flow.md` — branch e PR de implementação depois do merge deste plano.

Referências externas usadas para o adaptador:

- Current Weather: `https://openweathermap.org/api/current`
- Geocoding API: `https://openweathermap.org/api/geocoding-api`

O adaptador usa somente Geocoding direto e Current Weather 2.5. One Call API 4.0 não faz parte deste plano.

## Contrato alvo

### Stack e estrutura

- Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 sync, Alembic, PostgreSQL 16, httpx e uv.
- Arquitetura Hexagonal com as duas portas já registradas em D-002:
  - `WeatherProvider`;
  - `WeatherRepository`.
- Usar os módulos listados em **Arquivos permitidos e responsabilidade**. Não criar outros módulos, portas, camadas ou dependências sem novo plano aprovado.
- `domain/` importa somente biblioteca padrão e `typing`; `application/` importa somente `domain/`.
- FastAPI/Pydantic ficam na borda HTTP; SQLAlchemy fica no adaptador PostgreSQL; httpx fica no adaptador OpenWeather.

### Fluxo OpenWeather

1. Se `country` foi enviado, normalizá-lo para maiúsculas antes de consultar o provedor; cidade é aparada nas extremidades, mas preservada em caixa e acentuação para a consulta.
2. Consultar Geocoding direto por HTTPS:
   - com país: `GET /geo/1.0/direct?q=<city>,<country>&limit=5&appid=<key>`;
   - sem país: `GET /geo/1.0/direct?q=<city>&limit=5&appid=<key>`.
3. Geocoding retorna uma lista. Se vazia, lançar `CityNotFound`. Com país informado, selecionar o primeiro resultado cujo `country` corresponda ao código normalizado; sem país, selecionar o primeiro resultado. Se nenhum resultado corresponder ao país pedido, lançar `CityNotFound`.
4. Consultar Current Weather 2.5:
   `GET /data/2.5/weather?lat=<lat>&lon=<lon>&appid=<key>&units=metric&lang=pt_br`.
5. Construir `WeatherReading` com os campos mapeados abaixo e chamar o repository para upsert. O service não conhece URLs, parâmetros HTTP ou formato JSON externo.
6. Configurar `appid` pelo parâmetro de query usando `OPENWEATHER_API_KEY`; não concatenar manualmente URLs nem registrar URL/query string em logs.

Mapeamento obrigatório do JSON Current Weather para `WeatherReading`:

| Campo interno | Campo externo | Regra |
|---|---|---|
| `city_name` | `name` | Se ausente/vazio, usar `name` do resultado de geocoding selecionado. |
| `country_code` | `sys.country` | Senão, usar `country` do resultado de geocoding selecionado; sempre uppercase. |
| `latitude` | `coord.lat` | Se ausente, usar `lat` do geocoding selecionado. |
| `longitude` | `coord.lon` | Se ausente, usar `lon` do geocoding selecionado. |
| `temperature_c` | `main.temp` | Obrigatório; resposta inválida se ausente ou não numérico. `units=metric` torna o valor Celsius. |
| `feels_like_c` | `main.feels_like` | Opcional; `null` se ausente. |
| `humidity` | `main.humidity` | Obrigatório; inteiro entre 0 e 100, caso contrário resposta inválida. |
| `pressure_hpa` | `main.pressure` | Opcional; `null` se ausente. |
| `wind_speed_ms` | `wind.speed` | Opcional; `null` se ausente. `units=metric` torna o valor m/s. |
| `weather_main` | `weather[0].main` | Opcional; `null` se o array estiver ausente/vazio. |
| `weather_description` | `weather[0].description` | Opcional; `null` se o array estiver ausente/vazio. |
| `observed_at` | `dt` | Obrigatório; converter Unix seconds para datetime UTC. |
| `fetched_at` | — | Instante UTC da coleta, criado pela aplicação. |
| `source` | — | Constante `openweather`. |
| `raw_payload` | resposta JSON | JSON completo da Current Weather; somente persistência/auditoria, nunca resposta HTTP pública. |

JSON malformado, tipos inválidos nos campos obrigatórios, coordenadas inválidas ou ausência de resultados utilizáveis geram o erro correspondente; não preencher valores obrigatórios com defaults inventados.

### Endpoints

#### `POST /api/v1/weather/sync`

- Entrada JSON: `city` obrigatório, com tamanho de 1 a 120 caracteres; `country` opcional no formato ISO 3166-1 alpha-2.
- Campo `city` após trim não pode ser vazio; `country`, se enviado, deve conter exatamente duas letras ASCII.
- Executa o fluxo Geocoding → Current Weather definido acima.
- Faz upsert de uma única leitura por `(city_name, country_code, source)`.
- Retorna `200` com a representação pública de `WeatherReading` definida abaixo.

#### `GET /api/v1/weather`

- Filtros opcionais: `city` (igualdade case-insensitive após trim) e `country` (igualdade após uppercase).
- Paginação: `page` inteiro mínimo 1, padrão 1; `page_size` inteiro entre 1 e 100, padrão 20.
- Ordenação fixa: `observed_at DESC`; sem ordenação alternativa.
- Resposta: `{ "items": [...], "total": <int>, "page": <int>, "page_size": <int> }`.

#### `GET /api/v1/weather/{id}`

- `id` é UUID.
- Retorna `200` com a leitura correspondente.
- Retorna `404` com `reading_not_found` quando não existe.

#### Representação pública de `WeatherReading`

`POST /sync`, `GET /weather` e `GET /weather/{id}` usam os mesmos campos JSON:

```json
{
  "id": "uuid",
  "city_name": "São Paulo",
  "country_code": "BR",
  "latitude": -23.55052,
  "longitude": -46.633308,
  "temperature_c": 22.5,
  "feels_like_c": 23.0,
  "humidity": 70,
  "pressure_hpa": 1013,
  "wind_speed_ms": 3.2,
  "weather_main": "Clouds",
  "weather_description": "nuvens dispersas",
  "observed_at": "2026-11-17T19:00:00Z",
  "fetched_at": "2026-11-17T19:01:00Z",
  "source": "openweather"
}
```

Campos opcionais sem valor aparecem como `null`. `raw_payload` nunca é exposto. Temperaturas e medidas numéricas são serializadas como números JSON; timestamps em ISO 8601 UTC com sufixo `Z`.

#### `GET /health`

- Executa uma consulta mínima no banco.
- Retorna `200` com `{ "status": "ok", "database": "ok" }` quando íntegro.
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

Envelope obrigatório: `{ "error": "<code>", "details": { ... } }`. `details` contém somente:

- `validation_error`: `{"fields":[{"name":"<field>","reason":"<stable reason code>"}]}`; nunca incluir valor submetido pelo cliente.
- `city_not_found`: `{"city":"<trimmed city>","country":"<uppercase country or null>"}`.
- `reading_not_found`: `{"id":"<uuid>"}`.
- Demais códigos: `{}`.

Valores estáveis de `fields[].reason`: `required`, `blank`, `too_long`, `invalid_format`, `must_be_positive`, `out_of_range`, `invalid_uuid`. Mapeamento de validação: ausência de `city` → `required`; `city` vazio após trim ou filtro `city` vazio → `blank`; `city` acima de 120 caracteres → `too_long`; `country` diferente de duas letras ASCII → `invalid_format`; `page < 1` → `must_be_positive`; `page_size` fora de 1–100 → `out_of_range`; UUID de rota inválido → `invalid_uuid`. Geocoding `200 []` ou ausência de resultado para o país solicitado mapeia para `city_not_found`. HTTP 401, 429, timeout e 5xx de qualquer uma das duas chamadas externas usam os códigos da tabela; outros 4xx do provedor, JSON malformado ou estrutura inválida usam `provider_invalid_response`. O código interno nunca vaza chave, URL completa, payload externo ou detalhes brutos de exceção.

### Seed

O script `scripts/seed.py` grava exemplos diretamente no PostgreSQL, sem chamar a OpenWeather.

- Usa `source="openweather"` para respeitar a chave única existente.
- Realiza upsert pelas mesmas chaves usadas pelo sync.
- Permite repetir o comando sem duplicar cidades.
- Popula exatamente São Paulo, Rio de Janeiro e Curitiba, todos com `country_code="BR"`.
- Usa leituras sintéticas claramente identificáveis nos dados (descrição `seed data`) e timestamps UTC fixos; não chama API externa nem gera valores aleatórios.

## Decisões

- D-002: arquitetura Hexagonal enxuta com duas portas.
- D-004: persistência da última leitura por cidade, país e provedor.
- D-006: httpx como client da OpenWeather.
- D-009: envelope único de erros.
- D-011: seed local sem chamada externa.
- D-012: testes por camada.
- D-021: Geocoding direto antes da Current Weather 2.5; não usar One Call 4.0 nem o geocoder built-in por `q`.
- D-022: `raw_payload` é interno e não aparece em nenhuma resposta HTTP.

Decisões fechadas especificamente por este plano:

- **D-016 — estratégia do seed:** o seed usa `source="openweather"` e upsert pela mesma chave do sync.
- **D-017 — catálogo de erros:** os códigos e status da tabela acima.
- **D-018 — paginação:** `page=1`, `page_size=20`, máximo 100 e ordenação por `observed_at DESC`.
- **D-019 — retry do provedor:** timeout de 5 segundos e até 2 tentativas adicionais por chamada HTTP; retry em timeout, 429 e 5xx com espera fixa de 0,5 s e 1 s; sem retry em 401, 404 ou outros 4xx.
- **D-020 — payload bruto:** `raw_payload` é gravado em JSONB por padrão e nunca é usado como fonte de verdade.
- **D-022 — payload interno:** persistir `raw_payload`, mas excluí-lo dos schemas e respostas HTTP.

## Fora de escopo

- Histórico temporal de leituras.
- Autenticação ou autorização.
- Agendamento, filas, cache e múltiplos provedores.
- Deploy público.
- Frontend.
- Telemetria além dos logs básicos.
- Chamadas reais à OpenWeather no CI.

## Arquivos permitidos e responsabilidade

Somente criar ou alterar os caminhos listados nesta seção. Arquivo necessário que não esteja listado é bloqueio: interromper a implementação e abrir/ajustar plano antes de criá-lo.

### Projeto e execução

| Caminho | Responsabilidade permitida |
|---|---|
| `pyproject.toml` | Python 3.12, dependências runtime/dev listadas em `docs/architecture.md`, configuração pytest e Ruff; sem dependências extras. |
| `uv.lock` | Lock reproduzível gerado a partir do `pyproject.toml`. |
| `.env.example` | Adicionar/manter `OPENWEATHER_GEOCODING_BASE_URL`, base Current Weather, timeout e retries sem valores secretos. |
| `Dockerfile` | Instalar o projeto com uv e iniciar a API; sem ferramentas/dependências não listadas. |
| `docker-compose.yml` | Serviços `api` e `db` PostgreSQL 16, volume, healthcheck, porta configurável e espera do banco saudável. |
| `.repo-model.json` | Alterar `template` para `active` e preencher `validation_command` somente quando o comando existir e passar. |
| `.github/workflows/ci.yml` | Adicionar PostgreSQL 16 como service do job de validação e fornecer `TEST_DATABASE_URL`; conservar o job de bootstrap. |

Dependências permitidas: runtime `fastapi`, `uvicorn[standard]`, `sqlalchemy`, `psycopg[binary]`, `alembic`, `pydantic-settings`, `httpx`; desenvolvimento `pytest`, `respx`, `ruff`. Não adicionar SDK da OpenWeather, biblioteca de retry ou pacote de geocoding.

### Aplicação

| Caminho | Contrato/responsabilidade |
|---|---|
| `app/domain/models.py` | Dataclass `WeatherReading`, campos da tabela e tipos independentes de framework. |
| `app/domain/ports.py` | Somente `WeatherProvider` e `WeatherRepository` Protocols. Assinaturas: `fetch_current(city: str, country: str | None) -> WeatherReading`; `upsert(reading: WeatherReading) -> WeatherReading`; `list_readings(city: str | None, country: str | None, page: int, page_size: int) -> tuple[list[WeatherReading], int]`; `get_by_id(id: UUID) -> WeatherReading | None`; `check_health() -> None`, lançando `DatabaseUnavailable` se falhar. |
| `app/domain/errors.py` | Exceções de domínio necessárias: `CityNotFound`, `ProviderNotConfigured`, `ProviderAuthError`, `ProviderRateLimited`, `ProviderTimeout`, `ProviderInvalidResponse`, `ProviderUnavailable`, `ReadingNotFound` e `DatabaseUnavailable`. |
| `app/application/weather_service.py` | `sync_weather(city, country) -> WeatherReading`, `list_readings(city, country, page, page_size) -> tuple[list[WeatherReading], int]` e `get_reading(id) -> WeatherReading`; orquestra portas, lança `ReadingNotFound` se `get_by_id` retornar `None` e não importa adaptadores. |
| `app/adapters/outbound/openweather/client.py` | Implementa `WeatherProvider`; geocoding e current weather, validação/mapeamento JSON, timeout/retry D-019 e tradução de falhas externas. Coordenadas devem respeitar latitude -90..90 e longitude -180..180. |
| `app/adapters/outbound/postgres/models.py` | Modelo ORM correspondente somente à tabela `weather_readings`. |
| `app/adapters/outbound/postgres/session.py` | Engine/session SQLAlchemy, leitura de `DATABASE_URL` e fechamento de sessão. |
| `app/adapters/outbound/postgres/repository.py` | Implementa `WeatherRepository`, upsert, filtros, count + paginação, busca por UUID e health check. |
| `app/adapters/inbound/http/schemas.py` | Schemas Pydantic de entrada sync, leitura pública, paginação e health; `raw_payload` não consta em schema de saída. |
| `app/adapters/inbound/http/routes/weather.py` | Somente os três endpoints `/api/v1/weather`. |
| `app/adapters/inbound/http/routes/health.py` | Somente `GET /health`. |
| `app/adapters/inbound/http/dependencies.py` | Composition root FastAPI `Depends`, cria/injeta adaptadores e serviço. |
| `app/adapters/inbound/http/error_handlers.py` | Traduz erros de domínio e validação para envelope/códigos/status deste plano. |
| `app/config.py` | Settings tipadas para `APP_ENV`, `DATABASE_URL`, `OPENWEATHER_API_KEY`, bases externas, timeout, retries e `LOG_LEVEL`. |
| `app/main.py` | Cria FastAPI, registra rotas/handlers e mantém `/docs` e `/openapi.json`. |

### Banco, scripts, testes e documentação

| Caminho | Responsabilidade permitida |
|---|---|
| `alembic.ini` | Configuração Alembic ligada ao settings/URL do banco. |
| `alembic/env.py` | Metadata ORM e execução online de migrations; não cria schema por `create_all`. |
| `alembic/versions/0001_create_weather_readings.py` | Migration inicial da tabela descrita em `docs/architecture.md`; downgrade remove somente a tabela/índices criados pela revision. |
| `scripts/seed.py` | Upsert idempotente dos três registros fixos definidos neste plano. |
| `tests/conftest.py` | Fixtures compartilhadas: settings de teste, aplicação, `TestClient`, banco de integração e aplicação de migrations. |
| `tests/unit/test_models.py` | Testes de construção/validação do modelo de domínio, sem framework/DB. |
| `tests/unit/test_weather_service.py` | Fakes das duas portas; verifica delegação, upsert, filtros/paginação e leitura inexistente. |
| `tests/unit/test_openweather_client.py` | `respx` cobrindo Geocoding e Current Weather 2.5 sem rede real. |
| `tests/integration/test_migration.py` | Migration em banco vazio e constraints/índices previstos. |
| `tests/integration/test_weather_repository.py` | PostgreSQL real via `TEST_DATABASE_URL`: upsert, filtros, ordenação, paginação e UUID inexistente. |
| `tests/integration/test_weather_api.py` | Contratos HTTP com PostgreSQL e respostas externas interceptadas por `respx`; nunca usa rede real. |
| `tests/integration/test_health_api.py` | Health saudável e falha do repository/banco traduzida para 503. |
| `tests/integration/test_seed.py` | Execuções repetidas criam somente os três registros esperados. |
| `README.md` | Atualizar status, stack e instruções para a implementação concluída, sem duplicar documentação detalhada. |
| `docs/PROJECT.md` | Consultar; não alterar, pois o contrato de produto não muda neste plano. |
| `docs/decisions.md` | Consultar; não alterar. D-016 a D-022 ficam registrados no PR deste plano. Nova decisão necessária bloqueia a implementação até emenda aprovada. |
| `docs/architecture.md` | Conservar módulos, mapeamento e fluxo de duas chamadas definido neste plano. |
| `docs/getting-started.md` | Documentar env vars, sync, seed e comandos que realmente funcionam. |
| `docs/testing.md` | Registrar testes/fixtures reais, Postgres de teste e comandos executáveis. |
| `.github/workflows/ci.yml` | Ver linha de execução acima; validação via `scripts/run-validation.sh`. |

Não criar testes unitários de endpoint separados nem abstrações, portas, tabelas, endpoints, flags, endpoints de administração ou módulos além dos listados.

## RED → GREEN → REFACTOR

Após o merge deste plano, criar a worktree `feat/weather-api` a partir de `origin/develop` atualizada. Dentro dela, preparar primeiro o ambiente de teste com os arquivos de projeto, sincronizar dependências e criar stubs importáveis com assinaturas, tipos e rotas vazias para os módulos do primeiro estágio RED. Todo RED deve coletar e falhar por comportamento ausente, nunca por falta de pytest, configuração, conexão ao banco ou erro de importação.

### SETUP — ambiente reproduzível

- Criar `pyproject.toml` e configuração mínima de testes/lint conforme a lista permitida; gerar `uv.lock` a partir do manifesto.
- Comandos: `uv lock` e depois `uv sync --frozen`.
- Resultado: instalação reproduzível passa; nenhuma aplicação ou endpoint foi criado.
- Os stubs iniciais não contêm comportamento de domínio, SQL, HTTP externo ou tratamento de erros.

### RED 1 — domínio e serviço

- Arquivos: `tests/unit/test_weather_service.py`, `tests/unit/test_models.py`.
- Cenários: sync chama o provider uma vez e persiste uma leitura; falha do provider não chama repository; listagem passa filtros/paginação; UUID inexistente gera `ReadingNotFound`; `WeatherReading` mantém `source` e timestamps.
- Falha esperada: as specs coletam; a primeira asserção de comportamento falha porque os stubs não implementam a regra.
- Comando: `uv run pytest tests/unit/test_weather_service.py tests/unit/test_models.py`.

### GREEN 1

Criar somente os módulos `app/domain/*` e `app/application/weather_service.py` listados acima. Passar as specs focadas; não criar adaptadores HTTP ou banco nesta etapa.

### RED 2 — client OpenWeather

- Arquivo: `tests/unit/test_openweather_client.py`.
- Cenários: query geocoding com e sem país; seleção de resultado por país; lista vazia e sem país correspondente; parâmetros lat/lon e units/lang da Current Weather; mapeamento de cada campo da tabela; país/nome/coordenadas fallback; API key ausente; 401, 429, timeout, 5xx e JSON/campos obrigatórios inválidos.
- Verificar códigos/status e número de tentativas conforme D-019 e garantir que nenhuma chamada real aconteça. `respx` deve bloquear requests não registrados.
- Comando: `uv run pytest tests/unit/test_openweather_client.py`.

### GREEN 2

Criar `app/config.py` e `app/adapters/outbound/openweather/client.py`. Implementar apenas o protocolo em D-021 e o mapeamento explícito desta seção.

### RED 3 — migration e repository

- Arquivos: `tests/integration/test_weather_repository.py`, `tests/integration/test_migration.py`.
- Cenários: migration cria colunas/tipos/constraints/índice definidos em `docs/architecture.md`; migration downgrade remove objetos próprios; upsert duas vezes mantém uma linha e atualiza dados; filtros cidade/país; página e limite; UUID inexistente; health check.
- Banco: PostgreSQL 16 real isolado via `TEST_DATABASE_URL`; fixture aplica migration antes de cada suite e limpa os dados entre testes.
- Comando: `uv run pytest tests/integration/test_weather_repository.py tests/integration/test_migration.py`.

### GREEN 3

Criar somente migration, ORM, session e repository nos caminhos listados. Não usar `Base.metadata.create_all`.

### RED 4 — API e Docker

- Arquivos: `tests/integration/test_weather_api.py`, `tests/integration/test_health_api.py`.
- Cenários: status, schema e conteúdo exatos de cada endpoint; validação 422 para city vazia/country inválido/page inválida; envelope de erro de domínio; `raw_payload` ausente nas respostas; `/docs` e `/openapi.json`; health 200/503.
- Em sync, interceptar ambas as requisições OpenWeather com `respx` e uma base de teste, sem conectar ao hostname real.
- Comando: `uv run pytest tests/integration/test_weather_api.py tests/integration/test_health_api.py`.

### GREEN 4

Criar schemas, rotas, dependencies, error handlers, `app/main.py`, `Dockerfile`, `docker-compose.yml` e fixture compartilhada. Só expor endpoints listados neste plano.

### RED 5 — seed

- Arquivo: `tests/integration/test_seed.py`.
- Cenários: executar seed duas vezes deixa exatamente três linhas, com as mesmas chaves e conteúdo sintético fixo; a fixture de HTTP falha o teste se qualquer chamada externa for tentada.
- Comando: `uv run pytest tests/integration/test_seed.py`.

### GREEN 5

Criar `scripts/seed.py` e atualizar somente os docs listados na tabela de arquivos. Não adicionar novas rotas para seed.

### REFACTOR

Após todas as specs focadas ficarem verdes:

- remover duplicação de mapeamento entre domínio, ORM e schemas;
- manter Pydantic, SQLAlchemy e httpx fora do núcleo;
- revisar logs e garantia de que segredos não vazam;
- executar `uv run ruff check .`, `uv run ruff format --check .` e `uv run pytest`.

## Riscos

- A OpenWeather pode mudar ou omitir campos; o adaptador valida o contrato mínimo e rejeita payload inválido.
- Campos opcionais ausentes no provedor são `null`; campos obrigatórios ausentes ou coordenadas fora dos limites documentados geram `provider_invalid_response`.
- A migration usa os tipos e precisões fixados em `docs/architecture.md`.
- Retry pode ampliar o tempo total; D-019 limita a 2 retries por chamada, com esperas fixas de 0,5 s e 1 s.
- Dados de seed podem parecer dados reais; logs e documentação devem identificá-los como exemplos.
- Banco indisponível na inicialização deve falhar de forma explícita; o entrypoint aplica migration antes do Uvicorn.

## Configuração e infraestrutura

Aplicar somente os caminhos e responsabilidades da tabela **Arquivos permitidos e responsabilidade**. O `.repo-model.json` muda de `status: "template"` para `status: "active"` e recebe o `validation_command` somente no PR de implementação, depois que este comando existir e tiver sido executado com sucesso:

```bash
uv sync --frozen && uv run ruff check . && uv run ruff format --check . && uv run pytest
```

As migrations são aplicadas pela fixture de integração e pelo entrypoint/compose; não incluir `alembic upgrade head` no `validation_command` sem URL de banco explicitamente configurada.

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
