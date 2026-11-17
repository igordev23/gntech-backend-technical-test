# Git flow

Fluxo adaptado para um repositório solo de teste técnico. O objetivo é histórico legível, mudanças pequenas e revisão antes de integrar.

## Branches

| Branch | Origem | Destino | Uso |
|---|---|---|---|
| `main` | — | — | Estável; recebe releases |
| `develop` | `main` | — | Integração contínua |
| `feat/<slug>` | `develop` | `develop` | Feature de um plano |
| `fix/<slug>` | `develop` | `develop` | Correção de bug |
| `docs/<slug>` | `develop` | `develop` | Documentação |
| `chore/<slug>` | `develop` | `develop` | Manutenção/infra |
| `release/<versao>` | `develop` | `main` e `develop` | Preparação da entrega |
| `hotfix/<slug>` | `main` | `main` e `develop` | Correção urgente |

## Regras

- Uma branch por plano em `plans/`.
- Nada de commit direto em `main` ou `develop` depois da fundação.
- Mudanças de aplicação usam worktree dedicada.
- PR sempre para `develop`; release PR de `develop` para `main`.
- Commits seguem Conventional Commits.
- Não fazer force push em branches compartilhadas.
- Não commitar `.env`, segredos ou dados pessoais.

## Commits

Formato: `<tipo>(<escopo>): <descrição no imperativo>`.

Tipos: `feat`, `fix`, `docs`, `test`, `chore`, `refactor`, `ci`.

Mensagens de commit são 100% em inglês. Planos e documentação ficam em português.

Exemplos:

```text
chore: bootstrap repo model and governance
docs: define product scope and architecture
feat(api): add weather sync endpoint
test(client): cover openweather error mapping
```

## Fluxo de uma feature

```bash
git fetch origin
git worktree add -b feat/nome-curto ../worktrees/nome-curto origin/develop
cd ../worktrees/nome-curto
# implementar seguindo o plano
git add ...
git commit -m "feat(escopo): ..."
git push -u origin feat/nome-curto
# abrir PR para develop
```

## Release

```bash
git fetch origin
git worktree add -b release/1.0.0 ../worktrees/release-1.0.0 origin/develop
# ajustar versão, README, validação final
git push -u origin release/1.0.0
# PR release/1.0.0 -> main
# depois do merge, tag v1.0.0 em main
# merge de main de volta em develop
```

## Estado atual

- `main`: fundação do repositório.
- `develop`: criada a partir de `main` após a fundação.
- Nenhuma feature iniciada.
