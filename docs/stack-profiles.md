# Perfis de stack

Este repositório é neutro de stack. Escolha um perfil como ponto de partida, documente a escolha final em `architecture.md` e adapte o workflow de CI para instalar o runtime necessário antes da validação.

## Python / FastAPI (este projeto)

- Python 3.12, `pyproject.toml` e `uv.lock`.
- `uv sync --frozen` para instalar.
- `actions/setup-python` com 3.12 e `astral-sh/setup-uv` no CI.
- PostgreSQL 16 como service no CI para os testes de integração.
- `validation_command`: `uv sync --frozen && uv run ruff check . && uv run ruff format --check . && uv run pytest && docker build -t gntech-backend-technical-test:ci .`

## Node.js / TypeScript

- Adicione `package.json`, o lockfile e entradas específicas no `.gitignore`.
- Adicione `actions/setup-node` com a versão principal fixada no CI.
- Configure `validation_command` para, por exemplo: `npm ci && npm run typecheck && npm test && npm run build`.

## Python

- Adicione `pyproject.toml` e o lockfile escolhido.
- Adicione `actions/setup-python` com a versão de Python do projeto no CI.
- Configure `validation_command` para o comando do projeto, por exemplo: `uv sync --frozen && uv run pytest`.

## Go

- Adicione `go.mod` e `go.sum`.
- Adicione `actions/setup-go` com a versão declarada pelo projeto no CI.
- Configure `validation_command` para, por exemplo: `go test ./... && go vet ./...`.

## Site estático ou documentação

- Mantenha o modelo sem gerenciador de pacotes quando não houver build.
- Configure `validation_command` para um verificador útil de links, formatação ou artefatos gerados.

## Aplicações conteinerizadas

- Adicione `Dockerfile` e `.dockerignore` apenas quando o projeto entregar um container.
- Estenda o `validation_command` com o build da imagem, por exemplo: `docker build -t app:ci .`.

## Outras stacks

Use o mesmo contrato: manifesto de dependências versionado e lockfile quando o ecossistema suportar, runtime fixado no CI e um único `validation_command` que prova que o projeto pode ser entregue.
