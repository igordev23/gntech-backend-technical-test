# Registro de decisões

Este arquivo registra as decisões relevantes do projeto e, principalmente, **por que** cada uma foi tomada e **por que as alternativas foram descartadas**. O objetivo é duplo: o avaliador consegue revisar o raciocínio, e um agente de IA entende o contexto antes de propor mudanças.

## Regras

- Toda decisão que afeta contrato, arquitetura, dados, dependências ou operação entra aqui.
- Cada decisão registra contexto, escolha, motivo, alternativas rejeitadas e consequências.
- Decisão errada é **emendada**, não apagada: o caminho do raciocínio faz parte do registro.
- Status: `aceita`, `em revisão` ou `substituída por D-XXX`.
- A fonte canônica é este arquivo. Outros documentos resumem e apontam para o ID correspondente.

## Índice

| ID | Decisão | Status |
|---|---|---|
| D-001 | Python 3.12 + FastAPI | aceita |
| D-002 | Arquitetura Hexagonal (Ports & Adapters), 2 portas | aceita |
| D-003 | PostgreSQL 16 | aceita |
| D-004 | Última leitura por cidade, com upsert | aceita |
| D-005 | SQLAlchemy 2.0 sync + Alembic | aceita |
| D-006 | httpx como cliente HTTP | aceita |
| D-007 | uv + Python 3.12 | aceita |
| D-008 | Docker Compose local, sem deploy público | aceita |
| D-009 | Contrato de erro `{ error, details }` | aceita |
| D-010 | Sem autenticação | aceita |
| D-011 | Seed sem chamar a OpenWeather | aceita |
| D-012 | Testes por camada: pytest + respx + PostgreSQL real | aceita |
| D-013 | SDD, escopo travado e git flow | aceita |
| D-014 | Conteúdo em português, estrutura e código em inglês | aceita |
| D-015 | Repositório público `gntech-backend-technical-test` | aceita |

---

## D-001 — Python 3.12 + FastAPI

**Detalhes:** `docs/architecture.md` · **Status:** aceita

**Contexto.** O desafio pede uma API REST que consome uma API pública, persiste em banco relacional e entrega documentação. A escolha da linguagem foi feita pelo responsável pelo teste; este registro guarda a justificativa técnica que sustenta a escolha.

**Decisão.** Python 3.12 com FastAPI.

**Por quê.**

- O FastAPI gera OpenAPI/Swagger automaticamente — o enunciado pede API documentada; a documentação passa a ser consequência do código, não um artefato paralelo.
- Pydantic v2 valida entrada e saída e gera o schema do Swagger a partir do mesmo contrato, sem duplicação.
- `Depends` permite um composition root explícito, que é exatamente o ponto de montagem exigido pela arquitetura Hexagonal (D-002).
- `TestClient` testa a borda HTTP sem subir servidor.
- Endpoints síncronos rodam em threadpool, o que permite SQLAlchemy sync (D-005) sem bloquear o event loop.

**Alternativas rejeitadas.**

| Alternativa | Por que não |
|---|---|
| Django + DRF | Traz ORM, admin e migrations prontos, mas impõe MTV, settings global e mais cerimônia. Para 1 entidade e 4 endpoints o peso não se paga, e a estrutura do Django dificulta manter o núcleo independente do framework. |
| Flask | Leve, mas exige biblioteca extra para OpenAPI e validação manual. O contrato deixaria de ser gerado a partir do código. |
| NestJS (Node/TypeScript) | Viável, mas troca de runtime e ecossistema sem ganho para uma entidade; não havia requisito de TypeScript. |
| Go (chi/net/http) | Ótima performance e binário único, porém validação e OpenAPI exigem mais código manual — custo alto para o prazo curto do desafio. |
| Java + Spring Boot | Robusto e comum no mercado, mas o setup e o ciclo de feedback são mais longos do que o tamanho do desafio justifica. |

**Consequências.**

- Runtime fixado em 3.12 no Docker e no uv, independente da versão do host.
- Pydantic fica restrito à borda HTTP; o domínio usa dataclass (D-002).
- O time precisa conhecer Python/FastAPI para revisar — premissa aceita.

---

## D-002 — Arquitetura Hexagonal (Ports & Adapters), 2 portas

**Detalhes:** `docs/architecture.md` · **Status:** aceita

**Contexto.** A aplicação tem dois sistemas externos simétricos: OpenWeather (fonte) e PostgreSQL (persistência). É preciso que a regra de negócio seja testável sem infraestrutura e que a escolha seja defensável em entrevista.

**Decisão.** Hexagonal em versão enxuta: núcleo em `domain/` + `application/`, duas portas (`WeatherProvider`, `WeatherRepository`) e adaptadores de entrada/saída. O composition root é `adapters/inbound/http/dependencies.py`, usando `Depends`.

**Por quê.**

- FastAPI é um adaptador de entrada; `Depends` é o composition root natural para montar o serviço com os adaptadores.
- OpenWeather e PostgreSQL entram atrás de portas: trocar provedor ou banco não exige tocar na regra de negócio.
- O núcleo roda em teste com fakes, sem HTTP e sem banco.
- É proporcional: duas portas, sem unit of work, domain events, CQRS ou interfaces genéricas.

**Alternativas rejeitadas.**

| Alternativa | Por que não |
|---|---|
| Clean Architecture completa | Entidades + use cases + presenters + boundaries para 1 entidade e 4 endpoints viram cerimônia sem retorno. Hexagonal entrega a mesma inversão com menos conceitos. |
| Vertical Slice | Boa para muitas features; aqui existe basicamente uma feature (clima), e as fronteiras de infraestrutura ficariam menos explícitas. |
| Camadas tradicionais (controller → service → repository) | Genérica: não explica por que o FastAPI está ali nem como trocar OpenWeather/PostgreSQL sem tocar na regra. |
| MVC | FastAPI não é MVC; não há controller/view no sentido clássico. |
| DDD tático | O domínio é anêmico (uma leitura de clima). Aggregate e domain events não se pagam. |
| Tudo em `main.py` | Funciona, mas esconde as fronteiras e passa impressão de entrega júnior para uma vaga Pleno. |
| Interface para tudo | Inverter dependência de tudo o que se move só aumenta arquivos; o valor está nas duas fronteiras externas reais. |

**Consequências.**

- Mais arquivos do que o mínimo e mapeamento entre dataclass de domínio, modelo ORM e schema Pydantic.
- O núcleo não pode importar FastAPI, SQLAlchemy, httpx nem Pydantic — regra verificável em revisão.
- Se o escopo crescer para muitas features, reavaliar (o registro desta decisão deve ser emendado, não apagado).

---

## D-003 — PostgreSQL 16

**Detalhes:** `docs/architecture.md` · **Status:** aceita

**Contexto.** O enunciado pede persistência em banco relacional e execução reproduzível com Docker.

**Decisão.** PostgreSQL 16, uma única tabela.

**Por quê.**

- Atende ao pedido do enunciado sem adaptação.
- Tipos adequados ao problema: `TIMESTAMPTZ` para tempo, `NUMERIC` para temperatura, `UUID` nativo, `JSONB` para auditoria.
- Volume nomeado e healthcheck no Compose; service container no CI.
- `ON CONFLICT` implementa o upsert de D-004 de forma atômica.

**Alternativas rejeitadas.**

| Alternativa | Por que não |
|---|---|
| SQLite | Simplifica a execução, mas foge do ambiente pedido e esconde diferenças de tipo, concorrência e operação que o avaliador quer ver. |
| MySQL | Equivalente para este desafio, sem vantagem sobre o PostgreSQL e sem o mesmo suporte a `JSONB`/`TIMESTAMPTZ`. |
| MongoDB | Não é relacional; contraria o enunciado. |
| Banco em memória | Não persiste — o requisito é persistência. |

**Consequências.**

- `docker compose` é necessário para rodar e para os testes de integração.
- O CI precisa de um serviço PostgreSQL.

---

## D-004 — Última leitura por cidade, com upsert

**Detalhes:** `docs/PROJECT.md`, `docs/architecture.md` · **Status:** aceita

**Contexto.** "Dados climáticos" poderia significar série temporal. O contrato definido é consultar a leitura mais recente por cidade.

**Decisão.** Uma linha por `(city_name, country_code, source)`, atualizada por `INSERT ... ON CONFLICT ... DO UPDATE`. Sem histórico.

**Por quê.**

- O caso de uso é "qual é o clima desta cidade agora"; histórico não é consultado em nenhum endpoint do escopo.
- Upsert é idempotente: sincronizar a mesma cidade duas vezes não duplica dado.
- `source` na chave prepara a inclusão de outro provedor sem migração de schema.
- Evita crescimento infinito e complexidade de paginação por leitura histórica.

**Alternativas rejeitadas.**

| Alternativa | Por que não |
|---|---|
| Histórico append-only | Exige mais dados, índices e endpoints que o pedido não menciona; aumenta o escopo sem melhorar a avaliação. |
| Uma linha por requisição de sync | Duplicaria cidades e tornaria a listagem ambígua. |
| Um `JSONB` por cidade com todo o payload | Perde colunas tipadas, `CHECK` e índices; dificulta consulta e validação. |
| Normalizar cidade em tabela própria | Com uma linha por cidade, o join não traz benefício. |

**Consequências.**

- Não há série temporal; se for necessária, é um novo plano com nova tabela/coluna.
- A constraint `UNIQUE (city_name, country_code, source)` é parte do contrato, não detalhe interno.

---

## D-005 — SQLAlchemy 2.0 sync + Alembic

**Detalhes:** `docs/architecture.md` · **Status:** aceita

**Contexto.** O adaptador PostgreSQL precisa de mapeamento tipado e schema versionado.

**Decisão.** SQLAlchemy 2.0 em modo síncrono, com Alembic para migrations.

**Por quê.**

- ORM tipado e amplamente conhecido, o que ajuda a revisão.
- Alembic versiona o schema: o banco do avaliador nasce igual ao do CI.
- Síncrono é suficiente: o gargalo é a chamada externa, não o volume de queries. Endpoints sync do FastAPI rodam em threadpool (D-001).
- Mantém o SQLAlchemy restrito ao adaptador de saída, como exige D-002.

**Alternativas rejeitadas.**

| Alternativa | Por que não |
|---|---|
| SQLAlchemy async | Exige engine/session async, mais cuidado com contexto e testes, sem ganho de throughput neste escopo. |
| SQLModel | Acopla Pydantic ao ORM e conflita com D-002 ("Pydantic só na borda"). |
| psycopg puro | SQL manual e mapeamento à mão; menos legível na revisão e mais propenso a erro. |
| `Base.metadata.create_all` sem Alembic | Sem versionamento de schema; o banco passaria a depender de código de aplicação. |

**Consequências.**

- O entrypoint do container aplica `alembic upgrade head` antes de subir a API.
- Testes de integração precisam aplicar migrations no banco de teste.

---

## D-006 — httpx como cliente HTTP

**Detalhes:** `docs/architecture.md` · **Status:** aceita

**Contexto.** O adaptador OpenWeather precisa de timeout, retry limitado e teste sem rede.

**Decisão.** `httpx`, com `respx` nos testes.

**Por quê.**

- Suporta chamadas síncronas e assíncronas, timeouts granulares e conexões reaproveitadas.
- `respx` intercepta `httpx` de forma limpa, sem mock de biblioteca de terceiros.
- É o cliente usado pelo ecossistema Starlette/FastAPI, então o time já o encontra no `TestClient`.

**Alternativas rejeitadas.**

| Alternativa | Por que não |
|---|---|
| `requests` | Sem caminho async e sem o mesmo suporte de teste via `respx`. |
| `aiohttp` | Só assíncrono; mais cerimônia para o mesmo resultado. |
| SDK oficial da OpenWeather | Esconde o tratamento de erro HTTP que o desafio quer demonstrar e adiciona dependência de terceiro. |
| `urllib` | Manual demais: timeout, retry e mapeamento de erro ficariam todos por conta do código. |

**Consequências.**

- O client traduz 401, 404, 429, 5xx e timeout para erros de domínio.
- A URL completa da OpenWeather nunca vai para o log — a key vai na query string.

---

## D-007 — uv + Python 3.12

**Detalhes:** `docs/stack-profiles.md` · **Status:** aceita

**Contexto.** O projeto precisa de instalação reproduzível local e no CI.

**Decisão.** `uv`, com `pyproject.toml` e `uv.lock` versionados.

**Por quê.**

- Lockfile versionado e `uv sync --frozen` garantem as mesmas versões em qualquer máquina.
- Resolução e instalação rápidas, o que encurta o ciclo de feedback.
- Um único comando cobre dependências, execução de testes e ferramentas.

**Alternativas rejeitadas.**

| Alternativa | Por que não |
|---|---|
| pip + `requirements.txt` | Sem lock por padrão e resolução mais lenta. |
| Poetry | Bom, mas resolve e instala mais devagar e mantém formato próprio de lock. |
| pipenv | Menos adotado hoje e mais lento que uv. |
| conda | Pesado para um serviço Python simples. |

**Consequências.**

- `pyproject.toml` e `uv.lock` entram no repositório.
- O CI usa `astral-sh/setup-uv`.
- O runtime é 3.12, independente da versão de Python instalada no host.

---

## D-008 — Docker Compose local, sem deploy público

**Detalhes:** `docs/getting-started.md` · **Status:** aceita

**Contexto.** O enunciado pede containerização; a entrega é um teste técnico, não um produto.

**Decisão.** `docker compose up --build` sobe API + PostgreSQL na máquina do avaliador. Sem deploy público.

**Por quê.**

- Um comando reproduz o ambiente inteiro, incluindo banco e migrations.
- Sem custo de nuvem, domínio, TLS ou segredo em ambiente externo.
- O avaliador roda e inspeciona localmente, que é o fluxo esperado em avaliação.

**Alternativas rejeitadas.**

| Alternativa | Por que não |
|---|---|
| Deploy público (Render/Fly/Railway) | Custo, exposição de credenciais e manutenção além do pedido; não melhora a avaliação. |
| Só venv local, sem container | Não demonstra containerização, que é requisito do desafio. |
| Compose com banco em volume do host | Menos reproduzível que o volume nomeado e mais sujeito a conflito de porta/permissão. |

**Consequências.**

- Não há TLS, domínio, backup ou observabilidade de produção.
- Migrations rodam no entrypoint do container.

---

## D-009 — Contrato de erro `{ "error", "details" }`

**Detalhes:** `docs/PROJECT.md` · **Status:** aceita

**Contexto.** Erros de validação (422), de domínio (cidade não encontrada) e de infraestrutura (provedor indisponível) precisam de forma previsível.

**Decisão.** Envelope único: `{ "error": "codigo_snake", "details": { ... } }`, com status HTTP semântico.

**Por quê.**

- Forma estável e fácil de documentar no Swagger e consumir via `curl`.
- Separa o código de erro (testável, estável) do texto e dos detalhes.
- Não expõe o formato interno do framework.
- Permite um catálogo de códigos explícito, coberto por testes.

**Alternativas rejeitadas.**

| Alternativa | Por que não |
|---|---|
| RFC 9457 (`problem+json`) | Padrão maduro, mas com mais campos e semântica que o desafio não pede; adotar depois seria mudança de contrato, não refatoração. |
| `{ "detail": ... }` padrão do FastAPI | Mistura erro de validação do framework com erro de domínio e vaza detalhe interno. |
| Texto livre | Impossível de consumir e de testar de forma estável. |

**Consequências.**

- Um handler global normaliza `RequestValidationError` para o mesmo envelope.
- Erros inesperados não expõem stack trace nem payload do provedor.

---

## D-010 — Sem autenticação

**Detalhes:** `docs/PROJECT.md` · **Status:** aceita

**Contexto.** O enunciado não pede autenticação e não existe usuário final neste escopo.

**Decisão.** Nenhum mecanismo de autenticação ou autorização.

**Por quê.**

- Mantém a superfície mínima e o foco na avaliação de arquitetura, API e dados.
- Autenticação de fachada (chave estática) daria aparência de segurança sem ganho real.

**Alternativas rejeitadas.**

| Alternativa | Por que não |
|---|---|
| API key estática | Segurança de fachada; não protege nada em ambiente local e adiciona configuração. |
| JWT/OAuth2 | Exige usuários, emissão, refresh e testes — escopo muito maior que o pedido. |
| Login básico | Mesmo problema, sem caso de uso. |

**Consequências.**

- A API não deve ser exposta publicamente; isso fica explícito na documentação.
- Se houver deploy no futuro, autenticação vira um novo plano.

---

## D-011 — Seed sem chamar a OpenWeather

**Detalhes:** `docs/getting-started.md` · **Status:** aceita

**Contexto.** O avaliador precisa testar os GETs mesmo sem uma API key válida.

**Decisão.** Script de seed que grava leituras de exemplo sem chamada externa.

**Por quê.**

- Permite demonstrar a API completa sem depender de chave, rede ou cota.
- Torna a demonstração determinística.
- Separa "popular dados" de "integrar com provedor".

**Alternativas rejeitadas.**

| Alternativa | Por que não |
|---|---|
| Exigir API key para qualquer teste manual | Piora a experiência de quem avalia e depende de rede. |
| Apenas fixtures nos testes | Não popula o banco do `docker compose`, então os GETs ficariam vazios. |
| Seed automático no entrypoint | Efeito colateral escondido; dado de exemplo não deve aparecer sem pedido. |

**Consequências.**

- O plano 002 define como o seed convive com o `UNIQUE (city_name, country_code, source)` sem duplicar a mesma cidade na listagem — ponto ainda aberto.

---

## D-012 — Testes por camada: pytest + respx + PostgreSQL real

**Detalhes:** `docs/testing.md` · **Status:** aceita

**Contexto.** É preciso provar regra de negócio, integração HTTP e persistência sem tocar a API real.

**Decisão.**

- Núcleo: pytest com fakes das portas.
- Client OpenWeather: `respx`.
- Repository: PostgreSQL real, com migrations aplicadas.
- API: `TestClient` com adaptadores controlados.

**Por quê.**

- Cada camada é testada onde o risco está: SQL e constraints só são provados no banco real.
- Nenhum teste depende de rede, cota ou chave.
- Fakes no núcleo mantêm a suite rápida e o teste independente de infraestrutura.

**Alternativas rejeitadas.**

| Alternativa | Por que não |
|---|---|
| Mockar o repository em tudo | Não prova SQL, `ON CONFLICT` nem `CHECK`; o teste passaria com o banco quebrado. |
| Teste end-to-end contra a OpenWeather real | Instável, depende de cota e proibido pela regra de não tocar API real no CI. |
| Meta de 100% de cobertura | Métrica sem significado; o alvo é confiança nos comportamentos críticos. |

**Consequências.**

- O CI precisa de um service PostgreSQL.
- A suite de integração é mais lenta que a unitária — separação por pasta permite rodar só o necessário.

---

## D-013 — SDD, escopo travado e git flow

**Detalhes:** `AGENTS.md`, `docs/sdd.md`, `docs/git-flow.md` · **Status:** aceita

**Contexto.** Entrega solo, prazo curto e revisão humana por etapa, com agente de IA escrevendo código.

**Decisão.** Plano em `plans/` antes do código, mergeado via PR em `develop`; só depois abre-se o PR de implementação. Escopo travado (nada fora do plano), Conventional Commits e PR obrigatório para `develop` — inclusive para correções.

**Por quê.**

- O plano força decidir contrato e alternativas antes de escrever código.
- O PR do plano separado do PR de implementação faz a revisão do contrato acontecer antes de existir código para defender.
- O escopo travado impede que o agente expanda a entrega por conta própria.
- PR pequeno é revisável; histórico por branch mostra a evolução.
- O registro em `plans/` explica o "por quê" para quem avalia depois.

**Alternativas rejeitadas.**

| Alternativa | Por que não |
|---|---|
| Commits diretos em `main` | Sem revisão e sem ponto de rollback claro. |
| Implementar primeiro e documentar depois | O plano viraria justificativa retroativa; a revisão do contrato perderia o poder de barrar código errado. |
| Trunk-based sem feature flags | Exige CI forte e disciplina que não se paga em um teste solo. |
| Checklist informal | Não deixa registro do motivo nem do que foi descartado. |

**Consequências.**

- Mais documentação por mudança; o custo é aceito em troca de rastreabilidade.
- Cada mudança gera pelo menos dois PRs: plano e implementação.
- Correção também é PR, mesmo pequena.

---

## D-014 — Conteúdo em português, estrutura e código em inglês

**Detalhes:** `AGENTS.md` · **Status:** aceita

**Contexto.** O avaliador lê português; bibliotecas, convenções e mercado usam inglês. Nome de arquivo faz parte da estrutura do projeto, não do texto.

**Decisão.** Conteúdo de docs e planos em português. Nomes de arquivos e pastas (inclusive `docs/` e `plans/`), código, testes, identificadores, comentários, docstrings, logs e commits 100% em inglês.

**Por quê.**

- O avaliador revisa o raciocínio sem barreira de idioma.
- Identificadores em inglês seguem o padrão das bibliotecas e evitam mistura de línguas no mesmo arquivo.
- Nome de arquivo é estrutura, não conteúdo: `plans/001-repository-foundation.md` é navegável e consistente com o restante do projeto; `plans/001-fundacao-do-repo.md` misturaria idiomas no caminho.
- Mensagens de commit em inglês mantêm o histórico consistente com Conventional Commits.

**Alternativas rejeitadas.**

| Alternativa | Por que não |
|---|---|
| Tudo em português, inclusive nomes de arquivos e pastas | Mistura idioma no caminho, quebra a convenção de estrutura em inglês e gera link/import inconsistente. |
| Tudo em inglês, inclusive o conteúdo | Planos e justificativas ficariam menos claros para quem avalia. |

**Consequências.**

- Planos têm nome em inglês e conteúdo em português (ex.: `plans/002-weather-api.md`).
- A spec (arquivo de teste) é em inglês; a explicação dela no plano é em português.
- Revisão precisa checar os dois idiomas no lugar certo.

---

## D-015 — Repositório público `gntech-backend-technical-test`

**Detalhes:** `README.md` · **Status:** aceita

**Contexto.** A entrega precisa ser acessível ao avaliador sem atrito.

**Decisão.** Repositório público no GitHub, nome `gntech-backend-technical-test`.

**Por quê.**

- O nome deixa explícito que é teste técnico, não produto.
- Público permite abrir e clonar sem convite ou prazo de acesso.
- Sem segredos versionados: `.env` é gitignored e `.env.example` não tem valor real.

**Alternativas rejeitadas.**

| Alternativa | Por que não |
|---|---|
| Nome genérico (`weather-api`) | Não identifica a finalidade nem o contexto de avaliação. |
| Repositório privado com convite | Atrito e risco de o avaliador não conseguir acessar. |
| Repositório separado só para documentação | Sem ganho; separaria plano e código, que devem evoluir juntos. |

**Consequências.**

- Todo conteúdo é público: nada de segredo, PII ou dado de produção.
- O README precisa explicar status, escopo e como rodar.

---

## Decisões em aberto

Fechadas no plano 002, antes de qualquer código:

- Estratégia do seed em relação a `source` (D-011) para não duplicar cidade na listagem.
- Catálogo inicial de códigos de erro (D-009) e status HTTP correspondentes.
- Limites de paginação (`page`, `page_size`) e ordenação padrão.
- Política de retry/timeout do client (quantas tentativas, quais status, backoff).
- Formato do `raw_payload` e se ele é gravado por padrão.

## Como registrar uma decisão nova

1. Escolha o próximo ID (`D-016`, ...).
2. Preencha: contexto, decisão, por quê, alternativas rejeitadas, consequências.
3. Atualize o índice.
4. Se a decisão substituir outra, marque a antiga como `substituída por D-XXX` — não apague.
5. Atualize os documentos que apontam para o ID.
