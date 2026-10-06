# Enxoval Inteligente

O que comprar, quando e quanto para o bebê, do nascimento aos 12 meses.
Documentação: `docs/plano-enxoval.md` (produto) e `docs/superpowers/specs/` (desenho).

## Rodar localmente

Requisitos: Docker Desktop.

```bash
cp .env.example .env        # PowerShell: Copy-Item .env.example .env
# edite o .env e troque a senha
docker compose up -d --build
```

- API: http://localhost:8000/api/v1/saude
- Documentação da API: http://localhost:8000/api/docs

## Banco e conteúdo

```bash
docker compose run --rm api alembic upgrade head   # cria/atualiza as tabelas
docker compose run --rm api python -m seed         # carrega o conteúdo (só o que falta)
```

O conteúdo inicial fica em `api/seed/dados/`. Depois da primeira carga, edite pelo admin
(`/admin`): o seed só carrega uma tabela que ainda esteja vazia, então o que você apagar ou
renomear lá não volta. Para repor de propósito o que estiver faltando (sem sobrescrever o
que existe), rode `python -m seed --forcar`.

## Testes

```bash
docker compose run --rm api pytest
```
