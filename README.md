# Teste Técnico — API de Clima (GnTech)

Repositório do teste prático para a vaga de Desenvolvedor de Software Pleno na GnTech Exames.

O objetivo é demonstrar extração de dados de uma API pública, persistência em banco relacional, exposição dos dados via API REST documentada e execução reproduzível com Docker.

## Status

**Fundação do repositório.** Nenhum código de aplicação, dependência, container ou migration foi criado ainda. A implementação começa somente depois da aprovação do próximo plano em `plans/`.

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

## Como navegar

- `docs/PROJECT.md` — especificação do produto (fonte da verdade).
- `docs/architecture.md` — stack, camadas, modelo de dados e fluxos.
- `docs/decisions.md` — decisões, justificativas e alternativas descartadas.
- `docs/getting-started.md` — configuração e execução (estado alvo).
- `docs/testing.md` — estratégia de testes.
- `docs/sdd.md` — como uma mudança entra.
- `docs/git-flow.md` — branches, commits e PRs.
- `plans/` — planos aprovados, um por feature.
- `AGENTS.md` — regras duras para agentes de IA e humanos.

## Estrutura atual

```text
.
├── AGENTS.md
├── README.md
├── CONTRIBUTING.md
├── SECURITY.md
├── .env.example
├── .repo-model.json
├── docs/
│   ├── PROJECT.md
│   ├── architecture.md
│   ├── decisions.md
│   ├── getting-started.md
│   ├── testing.md
│   ├── sdd.md
│   ├── stack-profiles.md
│   └── git-flow.md
├── plans/
│   └── 001-repository-foundation.md
├── scripts/
│   ├── verify-repo.sh
│   └── run-validation.sh
└── .github/
    ├── workflows/ci.yml
    ├── ISSUE_TEMPLATE/bug.yml
    ├── dependabot.yml
    └── pull_request_template.md
```

## Próximos passos

1. Escrever e aprovar o próximo plano com o contrato da API, o DDL e a sequência RED → GREEN → REFACTOR.
2. Implementar a fundação técnica (pyproject/uv, Docker Compose, banco, migration, health).
3. Implementar sync, consulta, seed, testes e documentação de execução.
4. Ativar o `.repo-model.json` (`template` → `active`) e fechar a release `1.0.0`.

## Regra de escopo

Nada fora do plano aprovado em `plans/` é implementado. Necessidade nova vira plano novo, aprovado antes da execução. O plano entra por PR em `develop` e precisa ser mergeado antes do PR de implementação; correção também é PR. Ver `AGENTS.md`.
