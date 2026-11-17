# 001 — Fundação do repositório

## Origem

Pedido do responsável pelo teste para criar o repositório do desafio técnico da GnTech seguindo o modelo `repo-blueprint`, antes de qualquer implementação.

## Problema

O projeto ainda não tem repositório, governança, escopo documentado nem fluxo de trabalho. Sem isso, a implementação começaria sem contrato e sem controle de escopo.

## Contrato alvo

- Repositório público `teste-tecnico-gntech` no GitHub.
- Modelo `repo-blueprint` completo: `IA.md`, `docs/`, `plans/`, `scripts/`, `.github/` e `.repo-model.json`.
- `.repo-model.json` em `status: "template"`; o CI valida apenas a estrutura.
- Regra dura de escopo travado documentada em `IA.md`.
- Git flow documentado em `docs/git-flow.md`; `main` com a fundação e `develop` criada a partir dela.
- Nenhum código de aplicação, dependência instalada, container, migration ou endpoint.

## Decisões

- **FastAPI + PostgreSQL + Docker local + OpenWeather**: stack alinhada ao pedido e ao enunciado.
- **Última leitura por cidade**: uma linha por `(city_name, country_code, source)`, com upsert.
- **SDD**: plano antes de código; contrato, RED, GREEN e REFACTOR.
- **Divisão A**: o agente escreve; o responsável revisa e aprova cada etapa.
- **Git flow adaptado**: `main`, `develop`, `feat/*`, `release/*`.
- **Idioma**: documentação e planos em português; código, testes e commits 100% em inglês.
- **Nenhuma instalação nesta etapa**: apenas arquivos de governança e documentação.

## Escopo desta etapa (arquivos)

- `IA.md`
- `README.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `opencode.json`
- `.repo-model.json`
- `.env.example`
- `.gitignore`
- `.gitattributes`
- `.dockerignore`
- `docs/PROJECT.md`
- `docs/architecture.md`
- `docs/getting-started.md`
- `docs/testing.md`
- `docs/sdd.md`
- `docs/stack-profiles.md`
- `docs/git-flow.md`
- `plans/001-fundacao-do-repo.md`
- `scripts/verify-repo.sh`
- `scripts/run-validation.sh`
- `.github/workflows/ci.yml`
- `.github/pull_request_template.md`
- `.github/ISSUE_TEMPLATE/bug.yml`
- `.github/dependabot.yml`

## Fora de escopo desta etapa

- `pyproject.toml`, `uv.lock`, `requirements.txt` ou qualquer dependência.
- `Dockerfile`, `docker-compose.yml` ou imagem.
- `app/`, `alembic/`, migrations, endpoints, seed ou testes de aplicação.
- Instalação de pacotes, build, container ou execução de migrations.

## RED → GREEN → REFACTOR

Não se aplica: mudança exclusivamente documental e de governança, sem código de aplicação. A validação é estrutural:

```bash
bash scripts/verify-repo.sh
git status --short
```

## Dados

Nenhuma tabela criada nesta etapa. O modelo alvo está em `docs/architecture.md`.

## API

Nenhum endpoint criado nesta etapa. O contrato alvo está em `docs/PROJECT.md`.

## Riscos

- **Escopo crescer antes da hora** → regra dura em `IA.md` e lista explícita de arquivos nesta etapa.
- **Documento divergir do código** → todo PR atualiza o plano e os docs afetados.
- **Vazar segredo** → `.env` gitignored; `.env.example` sem valores reais.
- **Git flow virar cerimônia** → branches curtas, um plano por feature, PR pequeno.

## Critério de pronto

- [ ] `bash scripts/verify-repo.sh` passa.
- [ ] `git status` limpo.
- [ ] Repositório remoto criado e `main` enviada.
- [ ] Branch `develop` criada e enviada.
- [ ] Nenhum pacote instalado, container ou código de aplicação.
