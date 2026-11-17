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

## Emenda — 2026-11-17 — AGENTS.md e arquitetura Hexagonal

Esta emenda não apaga a decisão anterior; ela registra a correção.

- `IA.md` foi renomeado para `AGENTS.md`, o padrão lido por agentes de IA. `opencode.json`, `scripts/verify-repo.sh`, `README.md` e `docs/sdd.md` foram atualizados.
- A arquitetura inicialmente descrita como "camadas pragmáticas" foi substituída por **Hexagonal (Ports & Adapters)** com duas portas: `WeatherProvider` e `WeatherRepository`.
- Justificativa: FastAPI é um adaptador de entrada e `Depends` é o composition root; OpenWeather e PostgreSQL são adaptadores de saída; o núcleo não importa FastAPI, SQLAlchemy, httpx nem Pydantic.
- A decisão completa e as alternativas rejeitadas estão em `docs/architecture.md` e em `AGENTS.md`.
- Nenhum código foi criado nesta emenda.

## Emenda — 2026-11-17 — Registro de decisões e nome do repositório

- Criado `docs/decisoes.md` como registro canônico: contexto, decisão, motivo, alternativas rejeitadas e consequências (D-001 a D-015), mais as decisões em aberto para o plano 002.
- `AGENTS.md`, `README.md`, `docs/sdd.md`, `CONTRIBUTING.md` e `docs/architecture.md` passaram a apontar para o registro; `scripts/verify-repo.sh` exige o arquivo.
- Repositório renomeado de `teste-tecnico-gntech` para `gntech-backend-technical-test` (nome em inglês). O GitHub redireciona a URL antiga; a pasta local acompanhou o nome.
- Nenhum código foi criado nesta emenda.

## Emenda — 2026-11-17 — Nomes de arquivos em inglês

- Arquivos e pastas seguem o padrão inglês; apenas o **conteúdo** dos docs e planos fica em português.
- `plans/001-fundacao-do-repo.md` → `plans/001-repository-foundation.md`.
- `docs/decisoes.md` → `docs/decisions.md`.
- Convenção atualizada em `AGENTS.md`, `README.md`, `CONTRIBUTING.md`, `docs/architecture.md` e `docs/decisions.md` (D-014).
- Referências atualizadas em `docs/sdd.md`, `docs/git-flow.md` e `scripts/verify-repo.sh`. Os nomes antigos nas emendas acima ficam como registro histórico.

## Emenda — 2026-11-17 — Plano mergeado antes da implementação

- Regra dura: nenhuma implementação começa antes do merge do PR do plano em `develop`.
- Plano e implementação usam PRs separados: `docs/<slug>` para o plano, `feat/<slug>` ou `fix/<slug>` para o código.
- Toda correção passa por PR próprio, mesmo pequena; nada direto em `develop` ou `main`.
- Regra registrada em `AGENTS.md`, `CONTRIBUTING.md`, `docs/git-flow.md`, `docs/sdd.md` e `docs/decisions.md` (D-013).
