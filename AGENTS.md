# AGENTS.md — Guia operacional para agentes de IA (e humanos)

> Repositório criado a partir do modelo `repo-blueprint`. As regras abaixo são a base. Instruções específicas do projeto podem complementar, mas nunca enfraquecer segurança, privacidade ou verificação.

> **REGRA DURA — ESCOPO TRAVADO.**
> Nenhuma alteração fora do plano aprovado em `plans/` é permitida. Se algo faltar, **pare e pergunte**.
> Não tome iniciativa por conta própria para:
>
> - adicionar, remover ou atualizar dependências;
> - criar, alterar ou remover endpoints, tabelas, colunas, migrations, arquivos ou pastas;
> - refatorar, renomear ou "melhorar" código fora do plano;
> - instalar pacotes, rodar builds, subir containers, executar migrations ou alterar o ambiente;
> - commitar ou dar push sem autorização explícita.
>
> Uma necessidade nova vira um novo plano em `plans/`, aprovado antes de qualquer execução.

## O que é

- Especificação autoritativa do produto: `docs/PROJECT.md`. Em conflito entre este arquivo, os docs e o `PROJECT.md`, o `PROJECT.md` vence.
- `README.md` é a visão geral para desenvolvedores; `docs/` guarda os detalhes. Este arquivo é o guia operacional curto.
- Toda feature chega com um plano próprio em `plans/`.
- Todo plano novo deve cumprir o padrão obrigatório de completude em `docs/sdd.md`; não iniciar implementação com escopo, contrato, arquivos ou validação ambíguos.
- Decisões de arquitetura, contrato, dados e dependências ficam em `docs/decisions.md`, com o motivo e as alternativas rejeitadas. Antes de propor mudança, leia o registro.
- Este é um teste técnico, não um produto em produção.

## Stack (alvo)

- Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 (sync), Alembic, PostgreSQL 16, httpx, uv.
- Testes: pytest + respx. Lint/format: Ruff.
- Docker + Docker Compose para execução local (API + PostgreSQL).

> A stack acima está documentada, mas **ainda não implementada**. Nenhum pacote foi instalado nesta etapa.

## Arquitetura — Hexagonal (Ports & Adapters)

- **Núcleo:** `domain/` (modelo, portas, erros) + `application/` (serviço).
- **Portas:** `WeatherProvider` e `WeatherRepository` (`typing.Protocol`).
- **Adaptadores de entrada:** FastAPI em `adapters/inbound/http/`.
- **Adaptadores de saída:** OpenWeather em `adapters/outbound/openweather/`; PostgreSQL em `adapters/outbound/postgres/`.
- **Composition root:** `adapters/inbound/http/dependencies.py`, usando `Depends`.
- **Regra de dependência:** o núcleo não importa FastAPI, SQLAlchemy, httpx nem Pydantic. Dependências apontam para dentro.
- **Proporcionalidade:** apenas 2 portas; sem Clean Architecture completa, unit of work, domain events, CQRS ou interfaces genéricas.
- **Testes:** núcleo com fakes; client HTTP com `respx`; repository com PostgreSQL; API com `TestClient`.

Detalhes e justificativa: `docs/architecture.md`.

### Estrutura alvo

```text
app/
├── domain/
│   ├── models.py          # WeatherReading (dataclass)
│   ├── ports.py           # WeatherProvider, WeatherRepository (Protocols)
│   └── errors.py
├── application/
│   └── weather_service.py
├── adapters/
│   ├── inbound/
│   │   └── http/
│   │       ├── routes/weather.py
│   │       ├── routes/health.py
│   │       ├── schemas.py
│   │       ├── dependencies.py
│   │       └── error_handlers.py
│   └── outbound/
│       ├── openweather/client.py
│       └── postgres/
│           ├── models.py
│           ├── repository.py
│           └── session.py
├── config.py
└── main.py
```

## Comandos (alvo, após implementação)

- Instalar: `uv sync --frozen`
- Rodar: `docker compose up --build`
- Testes: `uv run pytest` ou `docker compose run --rm api pytest`
- Lint/format: `uv run ruff check .` e `uv run ruff format --check .`
- Migrations: `uv run alembic upgrade head`

## Hard rules — não quebre

- **Escopo travado** (regra acima).
- Só commitar ou dar push com permissão explícita.
- Nunca commitar segredos: `.env` é gitignored; mantenha assim.
- Testes nunca tocam APIs reais, pagas ou compartilhadas. Fakes injetados por dependência; verificações reais são manuais, nunca no CI.
- Sem PII em logs, erros, planos, PRs ou comentários.
- Plano errado é emendado, não apagado — o caminho errado faz parte do registro.
- Toda mudança feita deve ser refletida no plano correspondente em `plans/`; código e plano não podem divergir.
- Toda decisão relevante é registrada em `docs/decisions.md` (contexto, escolha, motivo, alternativas rejeitadas, consequências). Decisão substituída é emendada, não apagada.
- Não instalar pacotes, rodar builds ou subir containers sem autorização explícita.
- Nenhuma implementação antes do merge do PR do plano em `develop`.
- Toda correção passa por PR próprio, mesmo pequena; nada direto em `develop` ou `main`.
- O núcleo (`domain/` e `application/`) não importa FastAPI, SQLAlchemy, httpx nem Pydantic.

## Fluxo obrigatório — plano antes de código

**Nenhuma implementação começa antes do merge do PR do plano em `develop`.**

1. **Plano primeiro.** Toda funcionalidade nova, correção ou mudança de comportamento começa com `plans/NNN-short-name.md`.
2. **PR do plano.** O plano vai em PR próprio (`docs/...`), sem código de aplicação.
3. **Merge do plano em `develop`.** Aprovado e mergeado, a implementação pode começar.
4. **PR de implementação.** Em PR separado (`feat/...` ou `fix/...`), referenciando o plano e o ID de decisão aplicável.
5. **Fix também é PR.** Correção nunca vai direto para `develop` nem para `main`; sempre branch + PR.

### Padrão obrigatório de qualidade do plano

- Listar os documentos de referência pelos caminhos exatos, sua autoridade e qual prevalece em caso de conflito.
- Definir o contrato observável: entradas, saídas, validações, defaults, erros/status e compatibilidade preservada.
- Enumerar cada caminho de arquivo permitido e sua responsabilidade. Não usar curingas, “arquivos relacionados”, “se necessário” ou “etc.” para deixar escopo implícito.
- Em integrações externas, citar a documentação oficial consultada e fixar produto/versão, método, rota, parâmetros, autenticação, formato de resposta/mapeamento, timeout, retry e tradução de erros.
- Fechar decisões que afetem contrato, arquitetura, dados, dependências ou comportamento antes do merge; registrar em `docs/decisions.md`. Questões ainda abertas devem ser marcadas como bloqueios e esclarecidas antes da aprovação.
- Para cada comportamento, informar spec, cenário, falha RED esperada, arquivos GREEN e comandos exatos. A falha RED não pode ser causada por ambiente ou erro de importação.
- Cobrir configuração, migração/downgrade, documentação, integração/CI, riscos com mitigação e critérios de aceite verificáveis.
- Não acrescentar à implementação qualquer comportamento, arquivo, dependência ou decisão que não esteja listado no plano aprovado. Se faltar algo, parar e solicitar esclarecimento ou aprovar emenda/plano novo antes de continuar.

Exceção: ajuste no próprio plano ainda em revisão pode entrar no mesmo PR do plano, porque nada foi mergeado. Depois do merge, qualquer ajuste é PR novo.

O plano fica no repositório como registro do que foi decidido, testado e por quê.

Para mudanças de aplicação, crie uma worktree dedicada antes da spec RED. Mudanças somente de documentação ou configuração trivial podem ficar no checkout principal, com validação registrada no plano.

## Git flow

- `main`: estável; recebe releases via PR de `develop`.
- `develop`: integração; recebe PRs de `feat/*`, `fix/*`, `docs/*` e `chore/*`.
- `feat/<slug>`, `fix/<slug>`, `docs/<slug>`, `chore/<slug>`: uma branch por mudança.
- PR de plano e PR de implementação são separados: o merge do plano em `develop` vem antes.
- `release/<versao>`: preparação da entrega; merge em `main` e de volta em `develop`.
- `hotfix/<slug>`: correção urgente a partir de `main`; merge em `main` e `develop`.
- Commits seguem Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`, `ci:`).
- Detalhes em `docs/git-flow.md`.

## Testing

Ver `docs/testing.md`. O objetivo é confiança para entregar, não número de cobertura. Testes rodam no CI (`.github/workflows/ci.yml`).

## Spec-driven development

Ver `docs/sdd.md`. Um plano não é checklist de implementação: ele identifica o contrato, a falha RED esperada, a menor mudança GREEN e o comando de verificação de cada comportamento.

## Convenções

- **Conteúdo da documentação e dos planos:** português.
- **Nomes de arquivos e pastas (inclusive `docs/` e `plans/`), código, testes e tudo que é executável:** 100% inglês — classes, funções, variáveis, colunas, campos de API, códigos de erro, logs, comentários, docstrings, nomes de testes, fixtures, assertions e mensagens de commit.
- O plano é escrito em português em um arquivo com nome em inglês (ex.: `plans/002-weather-api.md`); a spec (arquivo de teste) e o código que ela exercita são em inglês.
- Interfaces finas; regras de negócio em `application/`; acesso a infraestrutura isolado em adaptadores.
- Contratos definidos uma vez, nunca reescritos à mão em cada call site.
- Formato de erro: `{ "error": "codigo_snake", "details": { ... } }`.
- Timestamps em UTC (`TIMESTAMPTZ`).
