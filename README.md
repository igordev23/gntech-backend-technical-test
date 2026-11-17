# Teste Técnico — API de Clima (GnTech)

Repositório do teste prático para a vaga de Desenvolvedor de Software Pleno na GnTech Exames.

O objetivo é demonstrar extração de dados de uma API pública, persistência em banco relacional, exposição dos dados via API REST documentada e execução reproduzível com Docker.

## Status

**Release 1.0.0 pronto.** O código foi versionado em `1.0.0` (pyproject.toml) e validado localmente (tests, lint, format, Docker Compose). As mudanças principais incluem:

- API de clima com sync e consulta por cidade/país
- Adaptadores OpenWeather e PostgreSQL (Hexagonal, 2 portas)
- Migrações automáticas com Alembic
- Seed script para testes sem API key
- Cobertura de testes unitários e de integração
- Documentação governança (`AGENTS.md`, `docs/decisions.md`)

Variáveis de ambiente necessárias: `.env` com `OPENWEATHER_API_KEY`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`. Nunca commitar segredos.

## Decisões fechadas

Justificativa de cada escolha, alternativas descartadas e consequências: `docs/decisions.md`.

| Decisão | Escolha |
|---|---|
| Linguagem/framework | Python 3.12 + FastAPI |
| Arquitetura | Hexagonal (Ports & Adapters), 2 portas |
| Banco | PostgreSQL 16 |
| Dados | Última leitura por cidade (`upsert`), uma linha por `(city, country, source)` |
| API externa | OpenWeather (Current Weather) |
| Execução | Docker Compose local (API + PostgreSQL); sem deploy público |
| Processo | SDD: plano → contrato → RED → GREEN → REFACTOR |
| Git | `main` estável, `develop` de integração, `feat/*` por plano |
| Idioma | Conteúdo de docs/planos em português; nomes de arquivos, código, testes e commits 100% em inglês |

## API

- `POST /api/v1/weather/sync` — consulta a OpenWeather e persiste a leitura mais recente.
- `GET /api/v1/weather` — lista leituras com filtros e paginação.
- `GET /api/v1/weather/{id}` — consulta uma leitura por UUID.
- `GET /health` — verifica a conexão com PostgreSQL.
- Swagger: `/docs`.

Para configurar e executar localmente, consulte `docs/getting-started.md`.

## Estrutura

```text
app/
├── domain/ and application/
└── adapters/
    ├── inbound/http/
    └── outbound/{openweather,postgres}/
alembic/
scripts/seed.py
tests/{unit,integration}/
docs/
plans/
Dockerfile
docker-compose.yml
```

Documentação de produto: `docs/PROJECT.md`; decisões: `docs/decisions.md`; regras de contribuição: `AGENTS.md`.

## Regra de escopo

Nada fora do plano aprovado em `plans/` é implementado. Necessidade nova vira plano novo, aprovado antes da execução. O plano entra por PR em `develop` e precisa ser mergeado antes do PR de implementação; correção também é PR. Ver `AGENTS.md`.
