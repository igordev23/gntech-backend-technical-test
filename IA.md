# IA.md — Guia operacional para agentes de IA (e humanos)

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
- Este é um teste técnico, não um produto em produção.

## Stack & layout (alvo)

- Python 3.12, FastAPI, Pydantic v2, SQLAlchemy 2.0 (sync), Alembic, PostgreSQL 16, httpx, uv.
- Testes: pytest + respx. Lint/format: Ruff.
- Docker + Docker Compose para execução local (API + PostgreSQL).
- Camadas: `api/routes` → `services` → `clients` / `repositories` → `models`. Contratos em `schemas`; configuração e erros em `core`; sessão em `db`.

> A stack acima está documentada, mas **ainda não implementada**. Nenhum pacote foi instalado nesta etapa.

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
- Não instalar pacotes, rodar builds ou subir containers sem autorização explícita.

## Como uma feature entra

1. Escreva `plans/NNN-nome-curto.md` usando a estrutura de `docs/sdd.md`.
2. Defina o contrato alvo e escreva uma spec que falhe pelo motivo correto (RED).
3. Implemente a menor mudança que passa (GREEN) e refatore com a suite verde.
4. Atualize a documentação afetada.
5. O plano fica no repositório como registro do que foi decidido, testado e por quê.

Para mudanças de aplicação, crie uma worktree dedicada antes da spec RED. Mudanças somente de documentação ou configuração trivial podem ficar no checkout principal, com validação registrada no plano.

## Git flow

- `main`: estável; recebe releases via PR de `develop`.
- `develop`: integração; recebe PRs de `feat/*`, `fix/*`, `docs/*` e `chore/*`.
- `feat/<slug>`, `fix/<slug>`, `docs/<slug>`, `chore/<slug>`: uma branch por plano.
- `release/<versao>`: preparação da entrega; merge em `main` e de volta em `develop`.
- `hotfix/<slug>`: correção urgente a partir de `main`; merge em `main` e `develop`.
- Commits seguem Conventional Commits (`feat:`, `fix:`, `docs:`, `test:`, `chore:`, `refactor:`, `ci:`).
- Detalhes em `docs/git-flow.md`.

## Testing

Ver `docs/testing.md`. O objetivo é confiança para entregar, não número de cobertura. Testes rodam no CI (`.github/workflows/ci.yml`).

## Spec-driven development

Ver `docs/sdd.md`. Um plano não é checklist de implementação: ele identifica o contrato, a falha RED esperada, a menor mudança GREEN e o comando de verificação de cada comportamento.

## Convenções

- **Documentação e planos:** português.
- **Código, testes e tudo que é executável:** 100% inglês — nomes de arquivos e pastas, classes, funções, variáveis, colunas, campos de API, códigos de erro, logs, comentários, docstrings, nomes de testes, fixtures, assertions e mensagens de commit.
- O plano pode ser escrito em português; a spec (arquivo de teste) e o código que ela exercita são em inglês.
- Interfaces finas; regras de negócio em services; acesso a infraestrutura isolado.
- Contratos definidos uma vez, nunca reescritos à mão em cada call site.
- Formato de erro: `{ "error": "codigo_snake", "details": { ... } }`.
- Timestamps em UTC (`TIMESTAMPTZ`).
