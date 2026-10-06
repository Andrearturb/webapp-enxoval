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

## API

Documentação interativa em http://localhost:8000/api/docs (só com `DOCS_HABILITADO=true`).

```bash
# busca de cidade
curl "http://localhost:8000/api/v1/municipios?busca=curitiba"
# cria um enxoval e lê o resultado
curl -X POST http://localhost:8000/api/v1/enxovais -H 'Content-Type: application/json' \
  -d '{"municipio_codigo":4106902,"data_prevista":"2027-06-15","dias_entre_lavagens":2,
       "moradia":"apartamento","tem_carro":true,"orcamento":"intermediario","primeiro_filho":true}'
curl http://localhost:8000/api/v1/enxovais/<id>
```

## Front

```bash
docker compose up -d --build web
```

- http://localhost:5174

Gerar os tipos da API a partir do OpenAPI (a API precisa estar no ar, com `DOCS_HABILITADO=true`):
```bash
docker compose run --rm web npm run gen:api
```

### Testes

```bash
docker compose run --rm web npm test
```

## Testes

```bash
docker compose run --rm api pytest
docker compose run --rm web npm test
```
