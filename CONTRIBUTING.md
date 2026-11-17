# Contribuindo

Antes de implementar, registre a mudança em um plano dentro de `plans/` e siga o ciclo de `docs/sdd.md`: contrato, RED, GREEN e REFACTOR. Mantenha a alteração pequena, execute os comandos definidos pelo projeto e atualize o plano e a documentação afetados.

## Regra de escopo

Nenhuma alteração fora do plano aprovado é permitida. Se algo faltar, pare e pergunte. Não adicione dependências, endpoints, tabelas, arquivos ou refatorações por conta própria. Uma necessidade nova exige um novo plano aprovado.

## Git flow

- `main` é estável; `develop` é integração.
- Crie uma branch por mudança: `feat/`, `fix/`, `docs/` ou `chore/`.
- Plano e implementação em PRs separados: o PR do plano é mergeado em `develop` antes de qualquer código.
- Correção também abre PR (`fix/...`), mesmo pequena.
- Use worktree dedicada para mudanças de aplicação.
- Commits seguem Conventional Commits.
- Abra PR para `develop`; releases vão de `develop` para `main`.

Detalhes em `docs/git-flow.md`.

## Idioma

- Conteúdo de planos e documentação: português.
- Nomes de arquivos e pastas, código, testes, comentários, docstrings, identificadores e mensagens de commit: 100% inglês.

## Decisões

Decisão que afeta contrato, arquitetura, dados ou dependências vai para `docs/decisions.md`, com o motivo e as alternativas rejeitadas. O plano aponta para o ID da decisão.

## Antes do PR

- [ ] O plano em `plans/` descreve contrato, decisões e RED → GREEN → REFACTOR.
- [ ] Decisões novas ou alteradas estão em `docs/decisions.md`, com motivo e alternativas rejeitadas.
- [ ] A mudança está inteiramente dentro do plano.
- [ ] A validação definida em `.repo-model.json` passou.
- [ ] Não há segredo, PII ou dado de produção.
- [ ] A documentação afetada foi atualizada.

Não inclua segredos, dados pessoais ou respostas de produção em commits, issues ou pull requests.
