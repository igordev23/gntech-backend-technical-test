# Contribuindo

Antes de implementar, registre a mudança em um plano dentro de `plans/` e siga o ciclo de `docs/sdd.md`: contrato, RED, GREEN e REFACTOR. Mantenha a alteração pequena, execute os comandos definidos pelo projeto e atualize o plano e a documentação afetados.

## Regra de escopo

Nenhuma alteração fora do plano aprovado é permitida. Se algo faltar, pare e pergunte. Não adicione dependências, endpoints, tabelas, arquivos ou refatorações por conta própria. Uma necessidade nova exige um novo plano aprovado.

## Git flow

- `main` é estável; `develop` é integração.
- Crie uma branch por plano: `feat/`, `fix/`, `docs/` ou `chore/`.
- Use worktree dedicada para mudanças de aplicação.
- Commits seguem Conventional Commits.
- Abra PR para `develop`; releases vão de `develop` para `main`.

Detalhes em `docs/git-flow.md`.

## Idioma

- Planos e documentação: português.
- Código, testes, comentários, docstrings, identificadores e mensagens de commit: 100% inglês.

## Antes do PR

- [ ] O plano em `plans/` descreve contrato, decisões e RED → GREEN → REFACTOR.
- [ ] A mudança está inteiramente dentro do plano.
- [ ] A validação definida em `.repo-model.json` passou.
- [ ] Não há segredo, PII ou dado de produção.
- [ ] A documentação afetada foi atualizada.

Não inclua segredos, dados pessoais ou respostas de produção em commits, issues ou pull requests.
