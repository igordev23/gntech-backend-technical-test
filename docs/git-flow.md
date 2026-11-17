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

- Um plano por mudança; plano e implementação em PRs separados.
- O PR do plano entra em `develop` antes de qualquer código de implementação.
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

## Plano e implementação

1. Crie a branch `docs/<slug>` e abra o PR do plano em `plans/NNN-short-name.md`. Sem código de aplicação.
2. Merge do plano em `develop`.
3. Crie a branch `feat/<slug>` ou `fix/<slug>` a partir de `develop` atualizada.
4. Abra o PR de implementação, referenciando o plano.
5. Merge em `develop`.

Correção também é PR: `fix/<slug>`, nunca commit direto em `develop` ou `main`.

## Fluxo de uma feature

Pré-requisito: o PR do plano já foi mergeado em `develop`.

```bash
git fetch origin
git worktree add -b feat/short-name ../worktrees/short-name origin/develop
cd ../worktrees/short-name
# implementar seguindo o plano
git add ...
git commit -m "feat(escopo): ..."
git push -u origin feat/short-name
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

- `main`: contém a fundação do repositório; a release `1.0.0` ainda não foi mesclada.
- `develop`: contém a implementação do plano 002, integrada pelo PR #3.
- `feat/weather-api`: PR de implementação #3 mesclado.
- `release/1.0.0`: branch de release criada a partir de `develop` com versão bumpada e README atualizado.
- Release `1.0.0` pronto para revisão e merge para `main`.
