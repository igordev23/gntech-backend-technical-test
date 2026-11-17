# Spec-driven development

## Objetivo

SDD reduz ambiguidade antes do código. Uma mudança começa por um contrato observável e por uma spec que falha pelo motivo correto. A implementação só começa depois disso.

Use este fluxo para features, correções de comportamento, integrações e alterações com risco. Para ajustes exclusivamente editoriais ou de configuração trivial, registre a validação no plano sem forçar uma spec artificial.

## Regra de escopo

Nada fora do plano aprovado em `plans/` é implementado. Uma necessidade nova vira um novo plano, aprovado antes da execução. Ver `AGENTS.md`.

## Padrão obrigatório de completude do plano

Todo plano novo deve ser escrito para que outro implementador consiga executar o escopo sem escolher contratos ou inventar requisitos. Antes de abrir o PR do plano, confirme:

- **Fontes e autoridade:** caminhos exatos dos documentos consultados; indique a fonte autoritativa e como resolver conflitos. Leia `AGENTS.md`, `docs/PROJECT.md`, `docs/architecture.md`, `docs/decisions.md`, `docs/testing.md` e `docs/sdd.md` quando forem relevantes.
- **Contrato verificável:** entradas, saídas, tipos/campos, limites, defaults, normalização, erros e status HTTP. Defina também comportamento legado/compatibilidade.
- **Integrações externas:** fonte oficial e versão do produto; método e rota exatos; parâmetros e autenticação; estrutura de resposta e mapeamento campo-a-campo; timeouts, retries, status de retry e erros. Não deduzir rotas por nome de produto nem copiar formato de outra versão.
- **Arquivos fechados:** uma lista de caminhos exatos para criar/alterar, com ação e responsabilidade de cada arquivo. Não usar `src/*`, `app/`, “arquivos relacionados”, “se necessário” ou `etc.` como permissão aberta.
- **Decisões:** decisões relevantes já aceitas devem apontar para IDs em `docs/decisions.md`. Decisões novas devem ser registradas com contexto, escolha, motivo, alternativas rejeitadas e consequências. Não deixar contrato, arquitetura, dados ou dependências em aberto no plano aprovado.
- **RED → GREEN:** para cada comportamento, declarar arquivo(s) da spec, cenário, resultado observável, motivo exato da falha RED, comando focado e caminhos GREEN. Garantir que o RED não falha por setup, conexão, pacote ausente ou importação. Se necessário, planejar stubs importáveis sem comportamento antes de executar a spec.
- **Dados e operação:** schema/migration, constraints, estratégia de downgrade, configuração, segredos, execução local, CI e atualização documental correspondentes ao escopo.
- **Limites:** listar explicitamente o que fica fora. Se durante a implementação faltar um arquivo, decisão, dependência ou comportamento, parar; não ampliar o plano por inferência.
- **Aceite:** critérios objetivos que possam ser verificados por testes ou comandos, ligados aos comportamentos definidos.

Se uma fonte oficial não responder a uma questão necessária ou houver duas interpretações plausíveis, registrar a questão como bloqueio e obter decisão do responsável antes de aprovar/implementar. Não preencher lacunas com suposições silenciosas.

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
Pedido/issue e problema observável que motivam a mudança.

## Documentos de referência
- `AGENTS.md` — regras aplicáveis.
- `docs/PROJECT.md` — contrato de produto e precedência.
- `docs/architecture.md` — módulos, dependências e dados.
- `docs/decisions.md` — decisões existentes e IDs aplicáveis.
- `docs/testing.md` e `docs/sdd.md` — método de validação.
- Outros caminhos relevantes, com a informação usada de cada um.
- Fontes oficiais externas, quando houver integração, com produto/versão.

## Contrato alvo
- Entradas, tipos, obrigatoriedade, normalização, limites e defaults.
- Saídas com campos/tipos/formato e status HTTP.
- Erros: código estável, status e estrutura de `details`.
- Regras de negócio, compatibilidade e comportamento legado.
- Integrações: método/rota/params/auth, mapeamento de resposta, timeout/retry e erros.

## Decisões
- IDs aceitos em `docs/decisions.md`.
- Decisões novas com justificativa e alternativas.
- Questões em aberto: declarar bloqueio e responsável pela decisão; nenhum bloqueio de contrato pode seguir para aprovação.

## Escopo de arquivos
| Caminho exato | Ação (criar/alterar) | Responsabilidade e limite |
|---|---|---|
| `path/to/file` | criar | Comportamento permitido e exclusões relevantes |

## Fora de escopo
- Comportamentos, arquivos, dependências e refactors que não serão feitos.

## RED → GREEN → REFACTOR
### RED 1 — comportamento
- Arquivo(s) exato(s) da spec:
- Cenário/entrada:
- Resultado esperado:
- Falha RED esperada (sem falha de setup/importação):
- Comando exato:

### GREEN 1
Arquivos exatos e menor mudança que satisfaz a spec.

### REFACTOR 1
Limpeza segura após a spec passar; sem alterar contrato ou escopo.

## Dados, configuração e operação
- Migration/downgrade, variáveis, segredos, execução local e CI quando aplicável.

## Riscos e mitigação
- Risco observável → mitigação dentro do escopo.

## Critério de pronto
- [ ] Cada item de contrato possui teste/validação correspondente.
- [ ] Apenas os caminhos autorizados foram criados/alterados.
- [ ] Documentação e decisões refletem a implementação.
- [ ] RED, GREEN e comandos de validação ampla registrados com resultado.

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
