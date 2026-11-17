# Teste Técnico GnTech — API de Clima

Fonte da verdade do produto. Em conflito com qualquer outro documento, este vence.

## O que é

Uma API REST que coleta a leitura atual do clima de uma cidade na OpenWeather, persiste a última leitura no PostgreSQL e expõe os dados para consulta. É um teste técnico para a vaga de Desenvolvedor de Software Pleno da GnTech Exames, não um produto em produção.

O sistema demonstra, de ponta a ponta: requisição GET com parâmetros dinâmicos e API key, persistência em banco relacional com schema tipado, API REST documentada via Swagger e execução reproduzível com Docker Compose.

## Quem usa

- **Avaliador técnico:** sobe o ambiente, testa o sync e consulta os dados pelo Swagger ou por `curl`.
- **Desenvolvedor:** configura variáveis de ambiente, roda migrations, seed e testes.

Não há usuários finais, autenticação ou multiusuário nesta versão.

## Funcionalidades (contrato)

1. **Sincronizar leitura:** `POST /api/v1/weather/sync` recebe `city` (obrigatório) e `country` (opcional, ISO 3166-1 alpha-2), consulta a OpenWeather, valida a resposta e faz upsert da última leitura.
2. **Listar leituras:** `GET /api/v1/weather` lista as últimas leituras por cidade, com filtros opcionais de cidade/país e paginação.
3. **Consultar por ID:** `GET /api/v1/weather/{id}` retorna uma leitura específica.
4. **Health check:** `GET /health` verifica a API e a conexão com o banco.
5. **Documentação:** Swagger em `/docs` e OpenAPI em `/openapi.json`.
6. **Seed:** comando que insere leituras de exemplo para testar os GETs sem depender da OpenWeather.
7. **Docker local:** `docker compose up --build` sobe API + PostgreSQL, aplica migrations e expõe a API.

## Regras de negócio

- A tabela guarda **somente a última leitura** por `(city_name, country_code, source)`. Sync repetido atualiza a linha; não cria histórico.
- `observed_at` vem do provedor (`dt`); `fetched_at` é o momento da coleta. Ambos em UTC (`TIMESTAMPTZ`).
- A API key da OpenWeather vem de `OPENWEATHER_API_KEY`, nunca do código ou do Git.
- Sem API key, a aplicação sobe e os GETs funcionam com dados de seed; o sync responde 503 com erro claro.
- Erros seguem `{ "error": "codigo_snake", "details": { ... } }` e códigos HTTP semânticos.
- A tabela usa colunas tipadas. `raw_payload` é opcional e serve apenas para auditoria; não é fonte de verdade.
- Testes nunca chamam a OpenWeather real.

## Fora de escopo

- Histórico/série temporal de leituras (esta versão guarda apenas a última).
- Autenticação, autorização, usuários ou multi-tenant.
- Deploy público, domínio, TLS gerenciado ou ambiente de produção.
- Frontend, dashboard ou app mobile.
- Filas, cache, agendamento/cron ou múltiplos provedores de clima.
- Coleção Postman (o Swagger é o contrato).
- Observabilidade além de logs básicos e health check.

## Status

Fundação do repositório concluída. Implementação pendente de plano aprovado em `plans/`.
