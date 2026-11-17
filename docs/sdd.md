# Spec-driven development

## Objetivo

SDD reduz ambiguidade antes do código. Uma mudança começa por um contrato observável e por uma spec que falha pelo motivo correto. A implementação só começa depois disso.

Use este fluxo para features, correções de comportamento, integrações e alterações com risco. Para ajustes exclusivamente editoriais ou de configuração trivial, registre a validação no plano sem forçar uma spec artificial.

## Regra de escopo

Nada fora do plano aprovado em `plans/` é implementado. Uma necessidade nova vira um novo plano, aprovado antes da execução. Ver `AGENTS.md`.

## Sequência obrigatória

1. Crie ou atualize `plans/NNN-short-name.md` a partir do modelo abaixo.
2. Registre origem, contrato alvo, decisões já fechadas e compatibilidade esperada. Decisão que afeta contrato, arquitetura, dados ou dependência entra em `docs/decisions.md`, com o motivo e as alternativas rejeitadas.
3. Abra o PR do plano e faça merge em `develop` quando aprovado. Nenhum código de implementação antes desse merge.
4. Para mudanças de aplicação, abra uma worktree dedicada a partir de `develop` atualizada, antes da spec RED.
5. Escreva e execute a spec RED. A falha precisa demonstrar a ausência do comportamento, não erro de setup ou importação.
6. Faça a menor implementação GREEN e execute a spec focada.
7. Refatore apenas com a suite verde.
8. Execute a validação ampla do repositório e registre os comandos/resultados no plano e na PR de implementação.

## Registro de decisões

Toda decisão relevante vive em `docs/decisions.md`, com contexto, escolha, motivo, alternativas rejeitadas e consequências. O plano em `plans/` aponta para o ID da decisão em vez de repetir a justificativa. Decisão errada é emendada, não apagada — o histórico do raciocínio faz parte do registro.

## Worktree

Para mudanças de aplicação, parta de `develop` em uma worktree dedicada:

```bash
git fetch origin
git worktree add -b feat/short-name ../worktrees/short-name origin/develop
cd ../worktrees/short-name
git status --short
```

Troque `feat/` por `fix/`, `docs/` ou `chore/` quando apropriado. Não remova uma worktree sem verificar seu `git status`.

## Estrutura do plano SDD

```md
# NNN — Nome curto

## Origem
Issue, pedido ou plano que motivou a mudança.

## Contrato alvo
Entrada, saída, regras e comportamento legado preservado.

## Decisões
Escolhas fechadas e alternativas rejeitadas.

## RED → GREEN → REFACTOR
### RED 1 — comportamento
- Arquivo da spec:
- Cenário:
- Falha esperada:
- Comando:

### GREEN 1
Implementação mínima.

### REFACTOR 1
Limpeza segura após a spec passar.

## Riscos

## Critério de pronto
- [ ] RED executado e falhou pelo motivo esperado
- [ ] GREEN validado pela spec focada
- [ ] Suite ampla executada
- [ ] Documentação e integração atualizadas
```

## Idioma

O plano é escrito em português. A spec (arquivo de teste) e o código de produção são 100% em inglês.

## Paralelização

Divida trabalho apenas por contratos independentes. Cada pessoa ou agente recebe uma worktree e é dono de arquivos distintos. Não paralelize decisões de contrato ainda abertas, migrações que compartilham estado ou validações contra o mesmo ambiente.

## Critério de pronto

- Toda alteração de comportamento possui uma spec RED anterior ao código de produção.
- A falha RED foi causada pela ausência do comportamento esperado.
- As specs focadas e a validação ampla passam.
- Caminhos legados e no-op continuam cobertos quando aplicável.
- O plano, a PR e a documentação registram configuração, migração, rollback e riscos relevantes.
