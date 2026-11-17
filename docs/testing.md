# Testing

O objetivo é confiança para entregar, não número de cobertura.

## O que merece teste

- Mapeamento de erros do client OpenWeather: 404, 401, 429, timeout, 5xx e payload inválido.
- Regra de upsert da última leitura (idempotência: sync repetido não duplica).
- Contratos da API: sync, listagem com filtros/paginação, consulta por ID, 404 e health.
- Limite de escopo: sem API key, o sync retorna 503 e a API continua saudável.

## O que não merece

- Glue de framework que o typechecker/Pydantic já cobre.
- Chamadas reais à OpenWeather no CI. Use `respx` para simular o HTTP.
- Cobertura 100% artificial.

## Como

- Runner: `pytest`.
- Unitários: `tests/unit/` — client e service, com `respx` e fakes.
- Integração: `tests/integration/` — API com PostgreSQL de teste e client mockado.
- Banco de teste: `TEST_DATABASE_URL`; migrations aplicadas antes da suite.
- CI: `.github/workflows/ci.yml` sobe PostgreSQL 16 como service e roda o `validation_command` de `.repo-model.json`.
- Comando local: inicie `db` com Docker Compose, crie `weather_test` e execute `TEST_DATABASE_URL=postgresql+psycopg://weather:weather@localhost:5432/weather_test uv run pytest`.

## RED → GREEN

Cada comportamento novo chega com uma spec que falha pelo motivo esperado antes da implementação. O plano em `plans/` registra o arquivo da spec, o cenário, a falha esperada e o comando.

## Idioma

Nomes de testes, fixtures, assertions e comentários são 100% em inglês. A explicação no plano pode ficar em português.
