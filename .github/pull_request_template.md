## Contexto

Link para o plano em `plans/` e resumo curto da mudança.

## Escopo

- [ ] A mudança está inteiramente dentro do plano aprovado.
- [ ] Não há dependência, endpoint, tabela, arquivo ou refatoração fora do plano.

## Validação

- [ ] O plano descreve o contrato e as fases RED → GREEN → REFACTOR.
- [ ] Cada comportamento novo teve uma spec RED pelo motivo esperado.
- [ ] O comando de validação definido em `.repo-model.json` passou.
- [ ] Fluxo manual relevante foi verificado.

## Operação

- [ ] Não há migração, variável de ambiente ou passo de deploy novo.
- [ ] Há migração/configuração documentada abaixo.
- [ ] Não há PII, segredo ou dado de produção neste PR.

Descreva aqui migração, configuração, monitoramento e rollback quando aplicável.
