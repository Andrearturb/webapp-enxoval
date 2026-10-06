# Etapa 1 — Fundação (Docker, banco, modelos, seed, admin) · Plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Subir Postgres e a API em Docker Compose, criar todas as tabelas (catálogo e família) com Alembic, carregar o conteúdo do plano com um seed idempotente e deixar o conteúdo editável em `/admin`.

**Architecture:** API FastAPI em `api/`, com modelos SQLAlchemy 2 em `app/db/`, migrações em `api/alembic/` e seed em `api/seed/` (YAML + CSV do IBGE). Os testes rodam dentro do container `api` contra um banco de teste separado (`<POSTGRES_DB>_test`), com rollback por teste. O admin é o SQLAdmin, montado só quando `ADMIN_HABILITADO=true`.

**Tech Stack:** Docker Compose, PostgreSQL 17 (alpine), Python 3.12, FastAPI, SQLAlchemy 2, Alembic, psycopg 3, pydantic-settings, PyYAML, SQLAdmin, pytest, httpx.

**Spec:** [`docs/superpowers/specs/2026-10-05-enxoval-inteligente-design.md`](../specs/2026-10-05-enxoval-inteligente-design.md) · Conteúdo: [`docs/plano-enxoval.md`](../../plano-enxoval.md)

## Global Constraints

- Todo texto visível (mensagens de erro, rótulos do admin, conteúdo) em português do Brasil.
- Segredos só no `.env` (fora do git). `.env.example` só com nomes e valores de exemplo. `POSTGRES_PASSWORD` só com letras, números, `-` e `_` (vai dentro de uma URL).
- Postgres **sem porta publicada**. A API só publica `127.0.0.1:8000` no override de desenvolvimento.
- Itens e alertas de segurança nunca são removidos por orçamento ou preferência (a regra é aplicada no motor, Etapa 2; aqui o dado `e_seguranca` precisa existir e estar certo).
- Toda marca e regra de segurança nasce com `validado = false`.
- O seed **nunca sobrescreve** o que já existe no banco: depois da carga, o admin é a fonte da verdade.
- O seed nunca toca nas tabelas `enxoval` e `enxoval_linha`.
- Imagens Docker oficiais multi-arquitetura (`python:3.12-slim`, `postgres:17-alpine`).
- Todos os comandos são rodados na raiz do repositório. Eles funcionam no PowerShell e no Git Bash.
- Commits terminam com a linha `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

1. **Rodar o seed de novo depois de editar no admin** deve manter a edição (ex.: marca marcada como validada continua validada). Teste na Tarefa 8.
2. **Erro de digitação no YAML** (ex.: `prioridade: essencal`) deve falhar com mensagem que nomeia o item e os valores válidos, e não carregar meio catálogo. Teste na Tarefa 6.
3. **Busca sem acento**: "sao joao" precisa casar com "São João"; o campo `nome_busca` tem que ser normalizado igual nos dois lados. Teste na Tarefa 7.
4. **Municípios homônimos** (ex.: "Bom Jesus" existe em vários estados): a exceção de clima tem que acertar só o município da UF informada. Teste na Tarefa 7.
5. **Apagar uma marca no admin** que está ligada a itens deve remover só os vínculos, não os itens nem dar erro de chave estrangeira. Teste na Tarefa 3.

## Mapa de arquivos

```
.gitattributes                         # LF em scripts (evita quebra no container)
.env.example
docker-compose.yml                     # base: db + api
docker-compose.override.yml            # dev: volume do código, reload, porta local, banco de teste
db/init/01-banco-de-teste.sh           # cria <POSTGRES_DB>_test na primeira subida
README.md                              # como rodar
api/
├─ Dockerfile
├─ .dockerignore
├─ requirements.txt
├─ requirements-dev.txt
├─ pytest.ini
├─ alembic.ini
├─ alembic/env.py, script.py.mako, versions/*.py
├─ app/
│  ├─ __init__.py
│  ├─ config.py                        # Configuracoes, obter_configuracoes()
│  ├─ main.py                          # criar_app(cfg=None), app
│  ├─ rotas/__init__.py
│  ├─ rotas/saude.py                   # GET /api/v1/saude
│  ├─ admin/__init__.py                # montar_admin(app, engine)
│  └─ db/
│     ├─ __init__.py
│     ├─ base.py                       # Base, coluna_enum()
│     ├─ enums.py                      # todos os enums
│     ├─ sessao.py                     # obter_engine(), obter_sessao()
│     ├─ catalogo.py                   # modelos do catálogo
│     ├─ familia.py                    # Enxoval, EnxovalLinha
│     └─ modelos.py                    # importa todos os modelos (Alembic)
├─ seed/
│  ├─ __init__.py
│  ├─ __main__.py                      # python -m seed
│  ├─ util.py                          # ler_yaml, inserir_se_faltar, enum_de, buscar
│  ├─ base.py                          # categorias, fases, perfis, janelas, estados
│  ├─ itens.py                         # marcas, itens (+ tamanhos, regras, vínculos)
│  ├─ cidades.py                       # municípios, exceções, normalizar_busca
│  ├─ seguranca.py                     # regras de segurança + ligação com itens
│  ├─ carregar.py                      # carregar_tudo(sessao)
│  ├─ baixar_municipios.py             # baixa o CSV do IBGE (uso único)
│  └─ dados/*.yaml, municipios.csv
└─ tests/
   ├─ conftest.py
   ├─ test_saude.py
   ├─ test_banco.py
   ├─ test_catalogo.py
   ├─ test_familia.py
   ├─ test_admin.py
   └─ carga/test_base.py, test_itens.py, test_cidades.py, test_carregar.py  (sem __init__.py)
```

---

### Task 1: Esqueleto da API em Docker Compose com `/api/v1/saude`

**Files:**
- Create: `.gitattributes`, `.env.example`, `docker-compose.yml`, `docker-compose.override.yml`, `README.md`
- Create: `api/Dockerfile`, `api/.dockerignore`, `api/requirements.txt`, `api/requirements-dev.txt`, `api/pytest.ini`
- Create: `api/app/__init__.py`, `api/app/config.py`, `api/app/main.py`, `api/app/rotas/__init__.py`, `api/app/rotas/saude.py`
- Test: `api/tests/test_saude.py`

**Interfaces:**
- Produces: `app.config.Configuracoes` (campos `database_url: str`, `admin_habilitado: bool = False`, `docs_habilitado: bool = False`), `app.config.obter_configuracoes() -> Configuracoes` (cacheada), `app.main.criar_app() -> FastAPI`, `app.main.app`.

- [ ] **Step 1: Criar a infraestrutura**

`.gitattributes`:
```
* text=auto eol=lf
*.png binary
*.jpg binary
```

`.env.example`:
```
# Copie para .env e troque os valores. Nunca commite o .env.
# A senha vai dentro de uma URL: use só letras, números, - e _.
POSTGRES_USER=enxoval
POSTGRES_PASSWORD=troque-esta-senha
POSTGRES_DB=enxoval
ADMIN_HABILITADO=true
DOCS_HABILITADO=true
```

`docker-compose.yml`:
```yaml
services:
  db:
    image: postgres:17-alpine
    restart: unless-stopped
    environment:
      POSTGRES_USER: ${POSTGRES_USER:?defina POSTGRES_USER no .env}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?defina POSTGRES_PASSWORD no .env}
      POSTGRES_DB: ${POSTGRES_DB:?defina POSTGRES_DB no .env}
    volumes:
      - dados_db:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}"]
      interval: 5s
      timeout: 3s
      retries: 10

  api:
    build: ./api
    restart: unless-stopped
    environment:
      DATABASE_URL: postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}
      ADMIN_HABILITADO: ${ADMIN_HABILITADO:-false}
      DOCS_HABILITADO: ${DOCS_HABILITADO:-false}
    depends_on:
      db:
        condition: service_healthy

volumes:
  dados_db:
```

`docker-compose.override.yml`:
```yaml
# Carregado automaticamente pelo "docker compose" em desenvolvimento.
# Em produção usaremos só o docker-compose.yml (Etapa de deploy).
services:
  db:
    volumes:
      - ./db/init:/docker-entrypoint-initdb.d:ro
  api:
    environment:
      TEST_DATABASE_URL: postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB}_test
    volumes:
      - ./api:/app
    ports:
      - "127.0.0.1:8000:8000"
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

`db/init/01-banco-de-teste.sh` (roda só quando o volume do banco é criado pela primeira vez):
```sh
#!/bin/sh
set -e
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" \
  -c "CREATE DATABASE \"${POSTGRES_DB}_test\";"
```

`api/Dockerfile`:
```dockerfile
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt requirements-dev.txt ./
ARG INSTALAR_DEV=true
RUN pip install --no-cache-dir -r requirements.txt \
 && if [ "$INSTALAR_DEV" = "true" ]; then pip install --no-cache-dir -r requirements-dev.txt; fi
COPY . .
RUN useradd --create-home --uid 1000 app && chown -R app /app
USER app
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

`api/.dockerignore`:
```
__pycache__/
.pytest_cache/
*.pyc
```

`api/requirements.txt`:
```
fastapi>=0.115,<1
uvicorn[standard]>=0.30,<1
sqlalchemy>=2.0.30,<3
alembic>=1.13,<2
psycopg[binary]>=3.2,<4
pydantic-settings>=2.4,<3
pyyaml>=6,<7
sqladmin>=0.20,<1
```

`api/requirements-dev.txt`:
```
pytest>=8,<9
httpx>=0.27,<1
```

`api/pytest.ini`:
```ini
[pytest]
testpaths = tests
pythonpath = .
addopts = -q
```

`README.md`:
````markdown
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

## Testes

```bash
docker compose run --rm api pytest
```
````

Depois, crie o seu `.env`: `cp .env.example .env` (PowerShell: `Copy-Item .env.example .env`) e troque a senha.

- [ ] **Step 2: Escrever o teste que falha**

`api/tests/test_saude.py`:
```python
from fastapi.testclient import TestClient

from app.main import criar_app


def test_saude_responde_ok():
    cliente = TestClient(criar_app())

    resposta = cliente.get("/api/v1/saude")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok"}
```

- [ ] **Step 3: Rodar e ver falhar**

Run: `docker compose build api` e depois `docker compose run --rm api pytest`
Expected: FAIL com `ModuleNotFoundError: No module named 'app'`

- [ ] **Step 4: Implementar o mínimo**

`api/app/__init__.py` e `api/app/rotas/__init__.py`: arquivos vazios.

`api/app/config.py`:
```python
from functools import lru_cache

from pydantic_settings import BaseSettings


class Configuracoes(BaseSettings):
    """Lidas das variáveis de ambiente (DATABASE_URL, ADMIN_HABILITADO...)."""

    database_url: str
    admin_habilitado: bool = False
    docs_habilitado: bool = False


@lru_cache
def obter_configuracoes() -> Configuracoes:
    return Configuracoes()
```

`api/app/rotas/saude.py`:
```python
from fastapi import APIRouter

router = APIRouter(tags=["saúde"])


@router.get("/saude")
def saude() -> dict[str, str]:
    return {"status": "ok"}
```

`api/app/main.py`:
```python
from fastapi import APIRouter, FastAPI

from app.config import obter_configuracoes
from app.rotas import saude


def criar_app() -> FastAPI:
    cfg = obter_configuracoes()
    app = FastAPI(
        title="Enxoval Inteligente",
        docs_url="/api/docs" if cfg.docs_habilitado else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if cfg.docs_habilitado else None,
    )
    api = APIRouter(prefix="/api/v1")
    api.include_router(saude.router)
    app.include_router(api)
    return app


app = criar_app()
```

- [ ] **Step 5: Rodar e ver passar**

Run: `docker compose run --rm api pytest`
Expected: `1 passed`

- [ ] **Step 6: Subir o ambiente e conferir à mão**

Run: `docker compose up -d --build` e depois `curl http://localhost:8000/api/v1/saude`
Expected: `{"status":"ok"}`. Também: `docker compose ps` mostra `db` como `healthy` e **nenhuma porta publicada** para o `db`.

- [ ] **Step 7: Commit**

```bash
git add .gitattributes .env.example docker-compose.yml docker-compose.override.yml db README.md api
git commit -m "feat: esqueleto da API em Docker Compose com rota de saúde

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
Confirme antes, com `git status`, que o `.env` **não** está na lista.

---

### Task 2: Conexão com o banco, Alembic e fixtures de teste

**Files:**
- Create: `api/app/db/__init__.py`, `api/app/db/base.py`, `api/app/db/enums.py`, `api/app/db/sessao.py`, `api/app/db/modelos.py`
- Create: `api/alembic.ini`, `api/alembic/env.py`, `api/alembic/script.py.mako`, `api/alembic/versions/<id>_inicial.py`
- Create: `api/tests/conftest.py`, `api/tests/test_banco.py`
- Modify: `api/app/rotas/saude.py`, `api/tests/test_saude.py`

**Interfaces:**
- Consumes: `obter_configuracoes()` (Task 1).
- Produces: `app.db.base.Base` (DeclarativeBase com convenção de nomes), `app.db.base.coluna_enum(enum_cls) -> sqlalchemy.Enum`, `app.db.sessao.obter_engine() -> Engine`, `app.db.sessao.obter_sessao() -> Iterator[Session]` (dependência FastAPI), fixtures pytest `engine_teste` (sessão) e `sessao` (por teste, com rollback), `app.db.enums.*` (todos os enums abaixo).

- [ ] **Step 1: Criar base, enums, sessão e Alembic**

`api/app/db/__init__.py`: vazio.

`api/app/db/base.py`:
```python
from enum import StrEnum

from sqlalchemy import Enum, MetaData
from sqlalchemy.orm import DeclarativeBase

CONVENCAO_NOMES = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCAO_NOMES)


def coluna_enum(enum_cls: type[StrEnum]) -> Enum:
    """Enum gravado como texto (o valor, ex.: 'essencial'), validado no Python."""
    return Enum(
        enum_cls,
        native_enum=False,
        create_constraint=False,
        length=30,
        validate_strings=True,
        values_callable=lambda membros: [m.value for m in membros],
    )
```

`api/app/db/enums.py`:
```python
from enum import StrEnum


class Prioridade(StrEnum):
    ESSENCIAL = "essencial"
    UTIL = "util"
    PODE_ESPERAR = "pode_esperar"


class UsoClima(StrEnum):
    NEUTRO = "neutro"
    DIVIDE = "divide"
    SO_FRIO = "so_frio"


class Tamanho(StrEnum):
    RN = "RN"
    P = "P"
    M = "M"
    G = "G"
    GG = "GG"


class Condicao(StrEnum):
    COM_CARRO = "com_carro"
    SEM_CARRO = "sem_carro"
    APARTAMENTO = "apartamento"
    CASA_SEM_ESCADA = "casa_sem_escada"
    CASA_COM_ESCADA = "casa_com_escada"
    PERFIL_QUENTE = "perfil_quente"
    PERFIL_MODERADO = "perfil_moderado"
    PERFIL_FRIO = "perfil_frio"


class Efeito(StrEnum):
    INCLUIR_SO_SE = "incluir_so_se"
    MUDAR_PRIORIDADE = "mudar_prioridade"
    DICA = "dica"


class Faixa(StrEnum):
    ECONOMICO = "economico"
    INTERMEDIARIO = "intermediario"
    INVESTIR = "investir"


class PerfilCodigo(StrEnum):
    QUENTE = "quente"
    MODERADO = "moderado"
    FRIO = "frio"


class ReferenciaFase(StrEnum):
    GESTACAO_SEMANA = "gestacao_semana"
    BEBE_MES = "bebe_mes"


class TemaSeguranca(StrEnum):
    SONO = "sono"
    TRANSPORTE = "transporte"
    BANHO = "banho"
    ALIMENTACAO = "alimentacao"
    CASA = "casa"
    BRINQUEDOS = "brinquedos"
    GERAL = "geral"


class Moradia(StrEnum):
    APARTAMENTO = "apartamento"
    CASA_SEM_ESCADA = "casa_sem_escada"
    CASA_COM_ESCADA = "casa_com_escada"
```

`api/app/db/sessao.py`:
```python
from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session

from app.config import obter_configuracoes


@lru_cache
def obter_engine() -> Engine:
    return create_engine(obter_configuracoes().database_url, pool_pre_ping=True)


def obter_sessao() -> Iterator[Session]:
    with Session(obter_engine()) as sessao:
        yield sessao
```

`api/app/db/modelos.py`:
```python
"""Importa todos os módulos de modelos para registrá-los em Base.metadata.

O Alembic (env.py) importa este arquivo. Cada novo módulo de modelos entra aqui.
"""
```

Gere a estrutura do Alembic: `docker compose run --rm api alembic init alembic`. Depois, no `api/alembic.ini` gerado, deixe a linha da URL vazia: `sqlalchemy.url =`.

Substitua `api/alembic/env.py` inteiro por:
```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import obter_configuracoes
from app.db import modelos  # noqa: F401  (registra as tabelas)
from app.db.base import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

if not config.get_main_option("sqlalchemy.url"):
    # O configparser interpreta "%"; por isso o escape.
    config.set_main_option(
        "sqlalchemy.url", obter_configuracoes().database_url.replace("%", "%%")
    )

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    conectavel = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with conectavel.connect() as conexao:
        context.configure(
            connection=conexao, target_metadata=target_metadata, compare_type=True
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

Crie a migração inicial vazia: `docker compose run --rm api alembic revision -m "inicial"`.

- [ ] **Step 2: Escrever os testes que falham**

`api/tests/conftest.py`:
```python
import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

URL_TESTE = os.environ["TEST_DATABASE_URL"]


@pytest.fixture(scope="session")
def engine_teste():
    """Banco de teste zerado e migrado uma vez por execução do pytest."""
    engine = create_engine(URL_TESTE)
    with engine.begin() as conexao:
        conexao.execute(text("DROP SCHEMA public CASCADE"))
        conexao.execute(text("CREATE SCHEMA public"))
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", URL_TESTE.replace("%", "%%"))
    command.upgrade(cfg, "head")
    yield engine
    engine.dispose()


@pytest.fixture
def sessao(engine_teste):
    """Sessão cujo trabalho é desfeito no fim de cada teste."""
    conexao = engine_teste.connect()
    transacao = conexao.begin()
    sessao = Session(bind=conexao, join_transaction_mode="create_savepoint")
    yield sessao
    sessao.close()
    transacao.rollback()
    conexao.close()
```

`api/tests/test_banco.py`:
```python
from sqlalchemy import text


def test_migracoes_aplicadas_no_banco_de_teste(sessao):
    versoes = sessao.execute(text("SELECT count(*) FROM alembic_version")).scalar_one()
    assert versoes == 1
```

Substitua `api/tests/test_saude.py` por:
```python
from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db.sessao import obter_sessao
from app.main import criar_app


def _cliente_com_sessao(sessao) -> TestClient:
    app = criar_app()
    app.dependency_overrides[obter_sessao] = lambda: sessao
    return TestClient(app)


def test_saude_responde_ok_com_banco(sessao):
    resposta = _cliente_com_sessao(sessao).get("/api/v1/saude")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "banco": "ok"}


class _SessaoForaDoAr:
    def execute(self, *args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("conexão recusada"))


def test_saude_responde_503_sem_banco():
    resposta = _cliente_com_sessao(_SessaoForaDoAr()).get("/api/v1/saude")

    assert resposta.status_code == 503
    assert resposta.json() == {"status": "erro", "banco": "indisponivel"}
```

- [ ] **Step 3: Rodar e ver falhar**

Run: `docker compose run --rm api pytest`
Expected: os dois testes de saúde falham (a resposta ainda não tem `"banco"`); `test_migracoes_aplicadas_no_banco_de_teste` já passa. Se der `database "..._test" does not exist`, veja o Step 5.

- [ ] **Step 4: Implementar a saúde com banco**

`api/app/rotas/saude.py`:
```python
from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.sessao import obter_sessao

router = APIRouter(tags=["saúde"])


@router.get("/saude")
def saude(sessao: Session = Depends(obter_sessao)):
    try:
        sessao.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503, content={"status": "erro", "banco": "indisponivel"}
        )
    return {"status": "ok", "banco": "ok"}
```

- [ ] **Step 5: Rodar e ver passar**

Run: `docker compose run --rm api pytest`
Expected: `3 passed`.

Se aparecer `database "enxoval_test" does not exist`, o volume do banco foi criado antes do script de init. Confira primeiro se `db/init/01-banco-de-teste.sh` está com fim de linha LF (o `.gitattributes` garante isso nos próximos checkouts) e então recrie o volume **de desenvolvimento** (apaga só dados locais): `docker compose down -v` e `docker compose up -d`.

- [ ] **Step 6: Aplicar a migração no banco de desenvolvimento**

Run: `docker compose run --rm api alembic upgrade head` e depois `curl http://localhost:8000/api/v1/saude`
Expected: `{"status":"ok","banco":"ok"}`

- [ ] **Step 7: Commit**

```bash
git add api
git commit -m "feat: conexão com Postgres, Alembic e fixtures de teste

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Modelos do catálogo e migração

**Files:**
- Create: `api/app/db/catalogo.py`, `api/alembic/versions/<id>_catalogo.py` (gerado)
- Modify: `api/app/db/modelos.py`
- Test: `api/tests/test_catalogo.py`

**Interfaces:**
- Consumes: `Base`, `coluna_enum`, enums (Task 2).
- Produces (classes em `app.db.catalogo`): `Categoria`, `FaseRoteiro`, `Item`, `ItemTamanho`, `ItemRegra`, `JanelaTamanho`, `PerfilClima`, `Estado`, `Municipio`, `Marca`, `ItemMarca`, `RegraSeguranca`, tabela `item_regra_seguranca`. Relacionamentos: `Item.categoria`, `Item.fase_compra`, `Item.tamanhos`, `Item.regras`, `Item.marcas` (lista de `ItemMarca`), `Item.regras_seguranca`; `ItemMarca.marca`; `Marca.vinculos`; `RegraSeguranca.itens`; `ItemTamanho.fase_compra`; `Municipio.estado`.

- [ ] **Step 1: Escrever os testes que falham**

`api/tests/test_catalogo.py`:
```python
import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.catalogo import (
    Categoria,
    FaseRoteiro,
    Item,
    ItemMarca,
    ItemTamanho,
    Marca,
)
from app.db.enums import Faixa, Prioridade, ReferenciaFase, Tamanho, UsoClima


@pytest.fixture
def categoria_e_fase(sessao):
    categoria = Categoria(slug="roupas", nome="Roupas", ordem=1)
    fase = FaseRoteiro(
        codigo="gestacao_7_8m",
        nome="Do 7º ao 8º mês",
        referencia=ReferenciaFase.GESTACAO_SEMANA,
        inicio=27,
        fim=36,
        texto="Roupas RN e P.",
        ordem=3,
    )
    sessao.add_all([categoria, fase])
    sessao.flush()
    return categoria, fase


def _item(categoria, fase, **extra):
    dados = dict(
        slug="body",
        nome="Body",
        categoria=categoria,
        fase_compra=fase,
        prioridade_base=Prioridade.ESSENCIAL,
        uso_clima=UsoClima.DIVIDE,
        variante_frio="manga longa",
        variante_calor="manga curta",
        para_que_serve="Peça básica.",
        como_escolher="Algodão.",
    )
    dados.update(extra)
    return Item(**dados)


def test_item_com_tamanhos_e_valores_padrao(sessao, categoria_e_fase):
    categoria, fase = categoria_e_fase
    item = _item(categoria, fase)
    item.tamanhos.append(ItemTamanho(tamanho=Tamanho.RN, quantidade_base=4))
    sessao.add(item)
    sessao.flush()

    salvo = sessao.scalars(select(Item).where(Item.slug == "body")).one()
    assert salvo.categoria.nome == "Roupas"
    assert [t.tamanho for t in salvo.tamanhos] == [Tamanho.RN]
    assert salvo.e_seguranca is False
    assert salvo.escala_lavagem is False


def test_slug_de_item_e_unico(sessao, categoria_e_fase):
    categoria, fase = categoria_e_fase
    sessao.add(_item(categoria, fase))
    sessao.flush()
    sessao.add(_item(categoria, fase))
    with pytest.raises(IntegrityError):
        sessao.flush()


def test_item_que_divide_exige_as_duas_variantes(sessao, categoria_e_fase):
    categoria, fase = categoria_e_fase
    sessao.add(_item(categoria, fase, variante_calor=None))
    with pytest.raises(IntegrityError):
        sessao.flush()


def test_apagar_marca_remove_so_os_vinculos(sessao, categoria_e_fase):
    categoria, fase = categoria_e_fase
    marca = Marca(nome="Marca Teste", faixa_padrao=Faixa.ECONOMICO)
    item = _item(categoria, fase)
    item.marcas.append(ItemMarca(marca=marca, faixa=Faixa.ECONOMICO, ordem=1))
    sessao.add(item)
    sessao.flush()

    marca_id = marca.id
    assert marca.validado is False

    sessao.delete(marca)
    sessao.flush()
    sessao.expire_all()

    restante = sessao.scalars(select(Item).where(Item.slug == "body")).one()
    assert restante.marcas == []
    assert sessao.get(Marca, marca_id) is None
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `docker compose run --rm api pytest tests/test_catalogo.py`
Expected: FAIL com `ModuleNotFoundError: No module named 'app.db.catalogo'`

- [ ] **Step 3: Implementar os modelos**

`api/app/db/catalogo.py`:
```python
from datetime import date

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, coluna_enum
from app.db.enums import (
    Condicao,
    Efeito,
    Faixa,
    PerfilCodigo,
    Prioridade,
    ReferenciaFase,
    Tamanho,
    TemaSeguranca,
    UsoClima,
)


class Categoria(Base):
    __tablename__ = "categoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True)
    nome: Mapped[str] = mapped_column(String(80))
    ordem: Mapped[int] = mapped_column(default=0)

    def __str__(self) -> str:
        return self.nome


class FaseRoteiro(Base):
    """Fase do roteiro de compras; início e fim na unidade de `referencia`."""

    __tablename__ = "fase_roteiro"
    __table_args__ = (CheckConstraint("fim >= inicio", name="intervalo_valido"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(40), unique=True)
    nome: Mapped[str] = mapped_column(String(80))
    referencia: Mapped[ReferenciaFase] = mapped_column(coluna_enum(ReferenciaFase))
    inicio: Mapped[int]
    fim: Mapped[int]
    texto: Mapped[str] = mapped_column(Text)
    ordem: Mapped[int] = mapped_column(default=0)

    def __str__(self) -> str:
        return self.nome


item_regra_seguranca = Table(
    "item_regra_seguranca",
    Base.metadata,
    Column("item_id", ForeignKey("item.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "regra_seguranca_id",
        ForeignKey("regra_seguranca.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Item(Base):
    __tablename__ = "item"
    __table_args__ = (
        CheckConstraint(
            "quantidade IS NULL OR quantidade >= 1", name="quantidade_positiva"
        ),
        CheckConstraint(
            "uso_clima <> 'divide' OR "
            "(variante_frio IS NOT NULL AND variante_calor IS NOT NULL)",
            name="variantes_obrigatorias",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    nome: Mapped[str] = mapped_column(String(120))
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categoria.id"))
    fase_compra_id: Mapped[int] = mapped_column(ForeignKey("fase_roteiro.id"))
    para_que_serve: Mapped[str] = mapped_column(Text)
    como_escolher: Mapped[str] = mapped_column(Text)
    idade_inicio_meses: Mapped[int] = mapped_column(default=0)
    prioridade_base: Mapped[Prioridade] = mapped_column(coluna_enum(Prioridade))
    e_seguranca: Mapped[bool] = mapped_column(default=False)
    uso_clima: Mapped[UsoClima] = mapped_column(
        coluna_enum(UsoClima), default=UsoClima.NEUTRO
    )
    variante_frio: Mapped[str | None] = mapped_column(String(60))
    variante_calor: Mapped[str | None] = mapped_column(String(60))
    escala_lavagem: Mapped[bool] = mapped_column(default=False)
    quantidade: Mapped[int | None]
    unidade_texto: Mapped[str | None] = mapped_column(String(120))
    ordem: Mapped[int] = mapped_column(default=0)

    categoria: Mapped[Categoria] = relationship()
    fase_compra: Mapped[FaseRoteiro] = relationship()
    tamanhos: Mapped[list["ItemTamanho"]] = relationship(
        back_populates="item", cascade="all, delete-orphan", order_by="ItemTamanho.id"
    )
    regras: Mapped[list["ItemRegra"]] = relationship(
        back_populates="item", cascade="all, delete-orphan", order_by="ItemRegra.id"
    )
    marcas: Mapped[list["ItemMarca"]] = relationship(
        back_populates="item", cascade="all, delete-orphan", order_by="ItemMarca.ordem"
    )
    regras_seguranca: Mapped[list["RegraSeguranca"]] = relationship(
        secondary=item_regra_seguranca, back_populates="itens"
    )

    def __str__(self) -> str:
        return self.nome


class ItemTamanho(Base):
    __tablename__ = "item_tamanho"
    __table_args__ = (
        UniqueConstraint("item_id", "tamanho"),
        CheckConstraint("quantidade_base >= 0", name="quantidade_nao_negativa"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("item.id", ondelete="CASCADE"))
    tamanho: Mapped[Tamanho] = mapped_column(coluna_enum(Tamanho))
    quantidade_base: Mapped[int]
    # Fase de compra deste tamanho; vazio = usa a fase do item.
    fase_compra_id: Mapped[int | None] = mapped_column(ForeignKey("fase_roteiro.id"))

    item: Mapped[Item] = relationship(back_populates="tamanhos")
    fase_compra: Mapped[FaseRoteiro | None] = relationship()

    def __str__(self) -> str:
        return f"{self.tamanho}: {self.quantidade_base}"


class ItemRegra(Base):
    __tablename__ = "item_regra"
    __table_args__ = (UniqueConstraint("item_id", "condicao", "efeito"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("item.id", ondelete="CASCADE"))
    condicao: Mapped[Condicao] = mapped_column(coluna_enum(Condicao))
    efeito: Mapped[Efeito] = mapped_column(coluna_enum(Efeito))
    # mudar_prioridade: valor de Prioridade; dica: o texto; incluir_so_se: vazio.
    valor: Mapped[str | None] = mapped_column(String(500))

    item: Mapped[Item] = relationship(back_populates="regras")


class JanelaTamanho(Base):
    __tablename__ = "janela_tamanho"

    id: Mapped[int] = mapped_column(primary_key=True)
    tamanho: Mapped[Tamanho] = mapped_column(coluna_enum(Tamanho), unique=True)
    idade_inicio_dias: Mapped[int]
    idade_fim_dias: Mapped[int]
    peso_referencia: Mapped[str | None] = mapped_column(String(60))


class PerfilClima(Base):
    __tablename__ = "perfil_clima"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[PerfilCodigo] = mapped_column(coluna_enum(PerfilCodigo), unique=True)
    nome: Mapped[str] = mapped_column(String(60))
    descricao: Mapped[str] = mapped_column(Text)
    meses_frios: Mapped[list[int]] = mapped_column(JSON, default=list)
    meses_frescos: Mapped[list[int]] = mapped_column(JSON, default=list)

    def __str__(self) -> str:
        return self.nome


class Estado(Base):
    __tablename__ = "estado"

    uf: Mapped[str] = mapped_column(String(2), primary_key=True)
    nome: Mapped[str] = mapped_column(String(40))
    perfil_padrao: Mapped[PerfilCodigo] = mapped_column(coluna_enum(PerfilCodigo))

    def __str__(self) -> str:
        return self.nome


class Municipio(Base):
    __tablename__ = "municipio"

    codigo_ibge: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    nome: Mapped[str] = mapped_column(String(80))
    nome_busca: Mapped[str] = mapped_column(String(80), index=True)
    uf: Mapped[str] = mapped_column(ForeignKey("estado.uf"))
    perfil_excecao: Mapped[PerfilCodigo | None] = mapped_column(
        coluna_enum(PerfilCodigo)
    )

    estado: Mapped[Estado] = relationship()

    def __str__(self) -> str:
        return f"{self.nome}/{self.uf}"


class Marca(Base):
    __tablename__ = "marca"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), unique=True)
    faixa_padrao: Mapped[Faixa] = mapped_column(coluna_enum(Faixa))
    validado: Mapped[bool] = mapped_column(default=False)
    fonte: Mapped[str | None] = mapped_column(Text)
    revisado_em: Mapped[date | None] = mapped_column(Date)

    vinculos: Mapped[list["ItemMarca"]] = relationship(
        back_populates="marca", cascade="all, delete-orphan", passive_deletes=True
    )

    def __str__(self) -> str:
        return self.nome


class ItemMarca(Base):
    __tablename__ = "item_marca"
    __table_args__ = (UniqueConstraint("item_id", "marca_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("item.id", ondelete="CASCADE"))
    marca_id: Mapped[int] = mapped_column(ForeignKey("marca.id", ondelete="CASCADE"))
    faixa: Mapped[Faixa] = mapped_column(coluna_enum(Faixa))
    ordem: Mapped[int] = mapped_column(default=0)

    item: Mapped[Item] = relationship(back_populates="marcas")
    marca: Mapped[Marca] = relationship(back_populates="vinculos")


class RegraSeguranca(Base):
    __tablename__ = "regra_seguranca"
    __table_args__ = (
        CheckConstraint(
            "idade_fim_meses >= idade_inicio_meses", name="intervalo_valido"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(60), unique=True)
    tema: Mapped[TemaSeguranca] = mapped_column(coluna_enum(TemaSeguranca))
    idade_inicio_meses: Mapped[int]
    idade_fim_meses: Mapped[int]
    texto: Mapped[str] = mapped_column(Text)
    base: Mapped[str] = mapped_column(String(120))
    validado: Mapped[bool] = mapped_column(default=False)
    fonte: Mapped[str | None] = mapped_column(Text)
    revisado_em: Mapped[date | None] = mapped_column(Date)

    itens: Mapped[list[Item]] = relationship(
        secondary=item_regra_seguranca, back_populates="regras_seguranca"
    )

    def __str__(self) -> str:
        return self.codigo
```

Substitua `api/app/db/modelos.py` por:
```python
"""Importa todos os módulos de modelos para registrá-los em Base.metadata.

O Alembic (env.py) importa este arquivo. Cada novo módulo de modelos entra aqui.
"""
from app.db import catalogo  # noqa: F401
```

- [ ] **Step 4: Gerar e revisar a migração**

Run: `docker compose run --rm api alembic revision --autogenerate -m "catalogo"`

Abra o arquivo gerado em `api/alembic/versions/` e confira que ele cria **exatamente** estas 13 tabelas: `categoria`, `fase_roteiro`, `item`, `item_tamanho`, `item_regra`, `janela_tamanho`, `perfil_clima`, `estado`, `municipio`, `marca`, `item_marca`, `regra_seguranca`, `item_regra_seguranca`. Confira também as `CheckConstraint` (`quantidade_positiva`, `variantes_obrigatorias`, `quantidade_nao_negativa`, os dois `intervalo_valido`), os `ondelete="CASCADE"` e o índice `ix_municipio_nome_busca`. O `downgrade()` deve apagar tudo na ordem inversa. Se algo faltar, ajuste o arquivo à mão antes de seguir.

- [ ] **Step 5: Rodar e ver passar**

Run: `docker compose run --rm api pytest`
Expected: `7 passed` (3 anteriores + 4 novos).

- [ ] **Step 6: Aplicar no banco de desenvolvimento**

Run: `docker compose run --rm api alembic upgrade head`
Expected: termina sem erro, com a linha `Running upgrade ... -> ..., catalogo`.

- [ ] **Step 7: Commit**

```bash
git add api
git commit -m "feat: modelos do catálogo e migração

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Modelos da família (enxoval e linhas) e migração

**Files:**
- Create: `api/app/db/familia.py`, `api/alembic/versions/<id>_familia.py` (gerado)
- Modify: `api/app/db/modelos.py`
- Test: `api/tests/test_familia.py`

**Interfaces:**
- Consumes: `Municipio`, `Estado` (Task 3), enums `Moradia`, `Faixa`, `PerfilCodigo`.
- Produces: `app.db.familia.Enxoval` (id `uuid.UUID`, `municipio_codigo`, `perfil_clima`, `perfil_corrigido`, `data_prevista: date`, `dias_entre_lavagens: int` 1–7, `moradia`, `tem_carro`, `orcamento: Faixa`, `primeiro_filho`, `criado_em`, `atualizado_em`, `linhas`), `app.db.familia.EnxovalLinha` (PK `enxoval_id` + `chave: str`, `qtd_comprada`, `qtd_ganhada`, `qtd_ja_tinha` ≥ 0, `atualizado_em`).

- [ ] **Step 1: Escrever os testes que falham**

`api/tests/test_familia.py`:
```python
from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.db.catalogo import Estado, Municipio
from app.db.enums import Faixa, Moradia, PerfilCodigo
from app.db.familia import Enxoval, EnxovalLinha


@pytest.fixture
def curitiba(sessao):
    sessao.add(Estado(uf="PR", nome="Paraná", perfil_padrao=PerfilCodigo.FRIO))
    municipio = Municipio(
        codigo_ibge=4106902, nome="Curitiba", nome_busca="curitiba", uf="PR"
    )
    sessao.add(municipio)
    sessao.flush()
    return municipio


def _enxoval(municipio, **extra):
    dados = dict(
        municipio_codigo=municipio.codigo_ibge,
        perfil_clima=PerfilCodigo.FRIO,
        data_prevista=date(2027, 6, 15),
        dias_entre_lavagens=2,
        moradia=Moradia.APARTAMENTO,
        tem_carro=True,
        orcamento=Faixa.INTERMEDIARIO,
        primeiro_filho=True,
    )
    dados.update(extra)
    return Enxoval(**dados)


def test_enxoval_recebe_uuid_e_datas(sessao, curitiba):
    enxoval = _enxoval(curitiba)
    sessao.add(enxoval)
    sessao.flush()
    sessao.refresh(enxoval)

    assert len(str(enxoval.id)) == 36
    assert enxoval.criado_em is not None
    assert enxoval.perfil_corrigido is False


def test_apagar_enxoval_apaga_as_linhas(sessao, curitiba):
    enxoval = _enxoval(curitiba)
    enxoval.linhas.append(EnxovalLinha(chave="body:P:frio", qtd_comprada=3))
    sessao.add(enxoval)
    sessao.flush()

    sessao.delete(enxoval)
    sessao.flush()

    assert sessao.scalar(select(func.count()).select_from(EnxovalLinha)) == 0


def test_linha_comeca_zerada(sessao, curitiba):
    enxoval = _enxoval(curitiba)
    enxoval.linhas.append(EnxovalLinha(chave="berco::"))
    sessao.add(enxoval)
    sessao.flush()

    linha = enxoval.linhas[0]
    assert (linha.qtd_comprada, linha.qtd_ganhada, linha.qtd_ja_tinha) == (0, 0, 0)


@pytest.mark.parametrize("dias", [0, 8])
def test_dias_entre_lavagens_fora_de_1_a_7_e_recusado(sessao, curitiba, dias):
    sessao.add(_enxoval(curitiba, dias_entre_lavagens=dias))
    with pytest.raises(IntegrityError):
        sessao.flush()


def test_quantidade_negativa_e_recusada(sessao, curitiba):
    enxoval = _enxoval(curitiba)
    enxoval.linhas.append(EnxovalLinha(chave="body:P:frio", qtd_ganhada=-1))
    sessao.add(enxoval)
    with pytest.raises(IntegrityError):
        sessao.flush()
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `docker compose run --rm api pytest tests/test_familia.py`
Expected: FAIL com `ModuleNotFoundError: No module named 'app.db.familia'`

- [ ] **Step 3: Implementar os modelos**

`api/app/db/familia.py`:
```python
import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, coluna_enum
from app.db.enums import Faixa, Moradia, PerfilCodigo


class Enxoval(Base):
    """Respostas do questionário de uma família. A lista é recalculada na leitura."""

    __tablename__ = "enxoval"
    __table_args__ = (
        CheckConstraint(
            "dias_entre_lavagens BETWEEN 1 AND 7", name="dias_entre_lavagens_valido"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    municipio_codigo: Mapped[int] = mapped_column(ForeignKey("municipio.codigo_ibge"))
    perfil_clima: Mapped[PerfilCodigo] = mapped_column(coluna_enum(PerfilCodigo))
    perfil_corrigido: Mapped[bool] = mapped_column(default=False)
    data_prevista: Mapped[date] = mapped_column(Date)
    dias_entre_lavagens: Mapped[int] = mapped_column(SmallInteger)
    moradia: Mapped[Moradia] = mapped_column(coluna_enum(Moradia))
    tem_carro: Mapped[bool]
    orcamento: Mapped[Faixa] = mapped_column(coluna_enum(Faixa))
    primeiro_filho: Mapped[bool]

    linhas: Mapped[list["EnxovalLinha"]] = relationship(
        back_populates="enxoval", cascade="all, delete-orphan", passive_deletes=True
    )


class EnxovalLinha(Base):
    """Quantidades marcadas numa linha. `chave` = '<slug>:<tamanho>:<variante>'."""

    __tablename__ = "enxoval_linha"
    __table_args__ = (
        CheckConstraint(
            "qtd_comprada >= 0 AND qtd_ganhada >= 0 AND qtd_ja_tinha >= 0",
            name="quantidades_nao_negativas",
        ),
    )

    enxoval_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("enxoval.id", ondelete="CASCADE"), primary_key=True
    )
    chave: Mapped[str] = mapped_column(String(140), primary_key=True)
    qtd_comprada: Mapped[int] = mapped_column(default=0)
    qtd_ganhada: Mapped[int] = mapped_column(default=0)
    qtd_ja_tinha: Mapped[int] = mapped_column(default=0)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    enxoval: Mapped[Enxoval] = relationship(back_populates="linhas")
```

Em `api/app/db/modelos.py`, acrescente a linha:
```python
from app.db import familia  # noqa: F401
```

- [ ] **Step 4: Gerar e revisar a migração**

Run: `docker compose run --rm api alembic revision --autogenerate -m "familia"`
Confira que o arquivo cria só `enxoval` e `enxoval_linha`, com `ck_enxoval_dias_entre_lavagens_valido`, `ck_enxoval_linha_quantidades_nao_negativas` e a FK com `ondelete="CASCADE"`.

- [ ] **Step 5: Rodar e ver passar**

Run: `docker compose run --rm api pytest`
Expected: `13 passed`

- [ ] **Step 6: Aplicar no banco de desenvolvimento e commit**

Run: `docker compose run --rm api alembic upgrade head`

```bash
git add api
git commit -m "feat: modelos de enxoval e linhas da família

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Seed — utilitários e dados base (categorias, fases, perfis, janelas, estados)

**Files:**
- Create: `api/seed/__init__.py`, `api/seed/util.py`, `api/seed/base.py`
- Create: `api/seed/dados/categorias.yaml`, `fases.yaml`, `perfis.yaml`, `janelas.yaml`, `estados.yaml`
- Test: `api/tests/carga/test_base.py`

**Interfaces:**
- Consumes: modelos do catálogo (Task 3).
- Produces: `seed.util.PASTA_DADOS: Path`, `seed.util.ler_yaml(nome: str)`, `seed.util.inserir_se_faltar(sessao, modelo, linhas: list[dict], chave: list[str]) -> int`, `seed.util.enum_de(enum_cls, valor, contexto: str)`, `seed.util.buscar(mapa: dict, chave, contexto: str, tipo: str)`, `seed.base.carregar_base(sessao) -> dict[str, int]` (chaves: `categoria`, `fase_roteiro`, `perfil_clima`, `janela_tamanho`, `estado`; valor = linhas novas).

- [ ] **Step 1: Escrever os testes que falham**

A pasta se chama `tests/carga/` (e não `tests/seed/`) e **não** tem `__init__.py`, para não esconder o pacote `seed` de verdade.

`api/tests/carga/test_base.py`:
```python
import pytest
from sqlalchemy import select

from app.db.catalogo import Estado, FaseRoteiro, PerfilClima
from app.db.enums import PerfilCodigo, Prioridade
from seed.base import carregar_base
from seed.util import enum_de


def test_carga_base_insere_tudo(sessao):
    resumo = carregar_base(sessao)

    assert resumo == {
        "categoria": 7,
        "fase_roteiro": 8,
        "perfil_clima": 3,
        "janela_tamanho": 5,
        "estado": 27,
    }


def test_carga_base_e_idempotente(sessao):
    carregar_base(sessao)

    segunda = carregar_base(sessao)

    assert set(segunda.values()) == {0}


def test_perfis_e_estados_conforme_o_plano(sessao):
    carregar_base(sessao)

    frio = sessao.scalars(
        select(PerfilClima).where(PerfilClima.codigo == PerfilCodigo.FRIO)
    ).one()
    assert frio.meses_frios == [5, 6, 7, 8, 9]
    assert sessao.get(Estado, "PR").perfil_padrao == PerfilCodigo.FRIO
    assert sessao.get(Estado, "BA").perfil_padrao == PerfilCodigo.QUENTE
    assert sessao.get(Estado, "SP").perfil_padrao == PerfilCodigo.MODERADO
    ordens = sessao.scalars(select(FaseRoteiro.codigo).order_by(FaseRoteiro.ordem)).all()
    assert ordens[0] == "gestacao_ate_5m" and ordens[-1] == "bebe_9_12m"


def test_enum_de_explica_o_erro():
    with pytest.raises(ValueError, match="item 'body'.*essencal.*essencial, util, pode_esperar"):
        enum_de(Prioridade, "essencal", "item 'body'")
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `docker compose run --rm api pytest tests/carga`
Expected: FAIL com `ModuleNotFoundError: No module named 'seed'`

- [ ] **Step 3: Implementar utilitários e carga base**

`api/seed/__init__.py`: vazio.

`api/seed/util.py`:
```python
from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

PASTA_DADOS = Path(__file__).parent / "dados"


def ler_yaml(nome: str) -> Any:
    with open(PASTA_DADOS / nome, encoding="utf-8") as arquivo:
        return yaml.safe_load(arquivo)


def inserir_se_faltar(
    sessao: Session, modelo: type, linhas: list[dict], chave: list[str]
) -> int:
    """Insere as linhas que ainda não existem (pela chave). Nunca sobrescreve."""
    if not linhas:
        return 0
    comando = pg_insert(modelo).values(linhas).on_conflict_do_nothing(
        index_elements=chave
    )
    return sessao.execute(comando).rowcount


def enum_de[E: StrEnum](enum_cls: type[E], valor: Any, contexto: str) -> E:
    try:
        return enum_cls(valor)
    except ValueError:
        validos = ", ".join(m.value for m in enum_cls)
        raise ValueError(
            f"{contexto}: valor '{valor}' inválido; use um de: {validos}"
        ) from None


def buscar(mapa: dict, chave: Any, contexto: str, tipo: str) -> Any:
    try:
        return mapa[chave]
    except KeyError:
        raise ValueError(f"{contexto}: {tipo} '{chave}' não encontrado(a)") from None
```

`api/seed/base.py`:
```python
from sqlalchemy.orm import Session

from app.db.catalogo import Categoria, Estado, FaseRoteiro, JanelaTamanho, PerfilClima
from app.db.enums import PerfilCodigo, ReferenciaFase, Tamanho
from seed.util import enum_de, inserir_se_faltar, ler_yaml


def carregar_base(sessao: Session) -> dict[str, int]:
    categorias = ler_yaml("categorias.yaml")

    fases = [
        {**f, "referencia": enum_de(ReferenciaFase, f["referencia"], f"fase '{f['codigo']}'")}
        for f in ler_yaml("fases.yaml")
    ]
    perfis = [
        {**p, "codigo": enum_de(PerfilCodigo, p["codigo"], "perfil")}
        for p in ler_yaml("perfis.yaml")
    ]
    janelas = [
        {**j, "tamanho": enum_de(Tamanho, j["tamanho"], "janela")}
        for j in ler_yaml("janelas.yaml")
    ]
    estados = [
        {**e, "perfil_padrao": enum_de(PerfilCodigo, e["perfil_padrao"], f"estado {e['uf']}")}
        for e in ler_yaml("estados.yaml")
    ]

    return {
        "categoria": inserir_se_faltar(sessao, Categoria, categorias, ["slug"]),
        "fase_roteiro": inserir_se_faltar(sessao, FaseRoteiro, fases, ["codigo"]),
        "perfil_clima": inserir_se_faltar(sessao, PerfilClima, perfis, ["codigo"]),
        "janela_tamanho": inserir_se_faltar(sessao, JanelaTamanho, janelas, ["tamanho"]),
        "estado": inserir_se_faltar(sessao, Estado, estados, ["uf"]),
    }
```

`api/seed/dados/categorias.yaml`:
```yaml
- {slug: roupas, nome: Roupas, ordem: 1}
- {slug: sono-e-quarto, nome: Sono e quarto, ordem: 2}
- {slug: higiene-e-banho, nome: Higiene e banho, ordem: 3}
- {slug: passeio-e-transporte, nome: Passeio e transporte, ordem: 4}
- {slug: alimentacao, nome: Alimentação, ordem: 5}
- {slug: seguranca-da-casa, nome: Segurança da casa, ordem: 6}
- {slug: para-a-mae, nome: Para a mãe, ordem: 7}
```

`api/seed/dados/fases.yaml` (gestação em semanas; bebê em meses completos, `fim` incluso):
```yaml
- codigo: gestacao_ate_5m
  nome: Até o 5º mês de gestação
  referencia: gestacao_semana
  inicio: 0
  fim: 17
  ordem: 1
  texto: Definir o orçamento, pesquisar marcas e montar a lista de presentes. Por enquanto, comprar pouco.
- codigo: gestacao_5_7m
  nome: Do 5º ao 7º mês de gestação
  referencia: gestacao_semana
  inicio: 18
  fim: 26
  ordem: 2
  texto: Hora dos itens grandes — berço, colchão, cômoda com trocador, carrinho e bebê conforto.
- codigo: gestacao_7_8m
  nome: Do 7º ao 8º mês de gestação
  referencia: gestacao_semana
  inicio: 27
  fim: 36
  ordem: 3
  texto: Roupas RN e P, roupa de berço, higiene e fraldas; lavar tudo antes do parto. Mala da maternidade pronta e bebê conforto instalado até a 34ª semana.
- codigo: parto
  nome: Reta final e parto
  referencia: gestacao_semana
  inicio: 37
  fim: 42
  ordem: 4
  texto: Conferir a mala e descansar. O que faltar pode esperar o bebê chegar.
- codigo: bebe_0_3m
  nome: Do nascimento aos 3 meses
  referencia: bebe_mes
  inicio: 0
  fim: 2
  ordem: 5
  texto: Repor fraldas e comprar só o que fez falta, como sling ou bomba de leite. Roupas M para a estação certa.
- codigo: bebe_3_6m
  nome: Dos 3 aos 6 meses
  referencia: bebe_mes
  inicio: 3
  fim: 5
  ordem: 6
  texto: Roupas G, mordedores e tapete de atividades. No 5º mês, cadeira de alimentação, pratos, colheres e babadores.
- codigo: bebe_6_9m
  nome: Dos 6 aos 9 meses
  referencia: bebe_mes
  inicio: 6
  fim: 8
  ordem: 7
  texto: Começa a introdução alimentar, com copo de transição; roupas GG. Antes de engatinhar, protetor de tomada, trava de gaveta e portão.
- codigo: bebe_9_12m
  nome: Dos 9 aos 12 meses
  referencia: bebe_mes
  inicio: 9
  fim: 11
  ordem: 8
  texto: Primeiro sapato de sola flexível e roupas tamanho 1. Trocar a cadeirinha do carro só quando o bebê passar do limite do bebê conforto.
```

`api/seed/dados/perfis.yaml`:
```yaml
- codigo: quente
  nome: Quente o ano todo
  descricao: Sem inverno de verdade; só noites mais frescas em junho e julho.
  meses_frios: []
  meses_frescos: [6, 7]
- codigo: moderado
  nome: Inverno moderado
  descricao: Frio de junho a agosto, sem extremos.
  meses_frios: [6, 7, 8]
  meses_frescos: []
- codigo: frio
  nome: Inverno frio
  descricao: Frio de maio a setembro, com noites geladas.
  meses_frios: [5, 6, 7, 8, 9]
  meses_frescos: []
```

`api/seed/dados/janelas.yaml` (a grade muda entre marcas; só o RN tem peso de referência no plano):
```yaml
- {tamanho: RN, idade_inicio_dias: 0, idade_fim_dias: 30, peso_referencia: até cerca de 4 kg}
- {tamanho: P, idade_inicio_dias: 0, idade_fim_dias: 90, peso_referencia: null}
- {tamanho: M, idade_inicio_dias: 90, idade_fim_dias: 180, peso_referencia: null}
- {tamanho: G, idade_inicio_dias: 180, idade_fim_dias: 270, peso_referencia: null}
- {tamanho: GG, idade_inicio_dias: 270, idade_fim_dias: 365, peso_referencia: null}
```

`api/seed/dados/estados.yaml` (perfil padrão por estado; serras e exceções ficam em `excecoes_municipios.yaml`):
```yaml
- {uf: AC, nome: Acre, perfil_padrao: quente}
- {uf: AL, nome: Alagoas, perfil_padrao: quente}
- {uf: AP, nome: Amapá, perfil_padrao: quente}
- {uf: AM, nome: Amazonas, perfil_padrao: quente}
- {uf: BA, nome: Bahia, perfil_padrao: quente}
- {uf: CE, nome: Ceará, perfil_padrao: quente}
- {uf: DF, nome: Distrito Federal, perfil_padrao: moderado}
- {uf: ES, nome: Espírito Santo, perfil_padrao: quente}
- {uf: GO, nome: Goiás, perfil_padrao: moderado}
- {uf: MA, nome: Maranhão, perfil_padrao: quente}
- {uf: MT, nome: Mato Grosso, perfil_padrao: quente}
- {uf: MS, nome: Mato Grosso do Sul, perfil_padrao: moderado}
- {uf: MG, nome: Minas Gerais, perfil_padrao: moderado}
- {uf: PA, nome: Pará, perfil_padrao: quente}
- {uf: PB, nome: Paraíba, perfil_padrao: quente}
- {uf: PR, nome: Paraná, perfil_padrao: frio}
- {uf: PE, nome: Pernambuco, perfil_padrao: quente}
- {uf: PI, nome: Piauí, perfil_padrao: quente}
- {uf: RJ, nome: Rio de Janeiro, perfil_padrao: quente}
- {uf: RN, nome: Rio Grande do Norte, perfil_padrao: quente}
- {uf: RS, nome: Rio Grande do Sul, perfil_padrao: frio}
- {uf: RO, nome: Rondônia, perfil_padrao: quente}
- {uf: RR, nome: Roraima, perfil_padrao: quente}
- {uf: SC, nome: Santa Catarina, perfil_padrao: frio}
- {uf: SP, nome: São Paulo, perfil_padrao: moderado}
- {uf: SE, nome: Sergipe, perfil_padrao: quente}
- {uf: TO, nome: Tocantins, perfil_padrao: quente}
```

- [ ] **Step 4: Rodar e ver passar**

Run: `docker compose run --rm api pytest tests/carga`
Expected: `4 passed`

- [ ] **Step 5: Commit**

```bash
git add api/seed api/tests/carga
git commit -m "feat: seed idempotente dos dados base (categorias, fases, clima, estados)

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Seed — marcas e itens do plano

**Files:**
- Create: `api/seed/itens.py`, `api/seed/dados/marcas.yaml`, `api/seed/dados/itens.yaml`
- Test: `api/tests/carga/test_itens.py`

**Interfaces:**
- Consumes: `carregar_base` e utilitários (Task 5); modelos `Item`, `ItemTamanho`, `ItemRegra`, `ItemMarca`, `Marca`, `Categoria`, `FaseRoteiro`.
- Produces: `seed.itens.carregar_marcas(sessao) -> int`, `seed.itens.carregar_itens(sessao, dados: dict | None = None) -> dict[str, int]` (chaves `item`, `item_tamanho`, `item_regra`, `item_marca`). Item já existente (mesmo `slug`) é ignorado por inteiro, filhos incluídos.

**Decisões de conteúdo (registradas aqui para a validação):**
- Itens com `seguranca: true`: berço, colchão, lençol com elástico, bebê conforto, termômetro, protetor de tomada, trava de gaveta, portão e protetor de quina.
- A faixa de cada marca (`faixa` em `marcas.yaml`) é uma **primeira estimativa**, a validar. Um item pode sobrescrever a faixa de uma marca no próprio `itens.yaml`.
- Roupas RN e P compram-se no 7º–8º mês; M, G e GG nas fases do bebê (`fases_tamanho`).
- Sem carro: o bebê conforto continua, como `util`; o sling vira `essencial`.

- [ ] **Step 1: Escrever os testes que falham**

`api/tests/carga/test_itens.py`:
```python
import pytest
from sqlalchemy import func, select

from app.db.catalogo import Item, Marca
from app.db.enums import Condicao, Efeito, Faixa, Prioridade, Tamanho, UsoClima
from seed.base import carregar_base
from seed.itens import carregar_itens, carregar_marcas

ITENS_DE_SEGURANCA = {
    "berco", "colchao-berco", "lencol-elastico", "bebe-conforto", "termometro",
    "protetor-tomada", "trava-gaveta", "portao-seguranca", "protetor-quina",
}


@pytest.fixture
def catalogo(sessao):
    carregar_base(sessao)
    carregar_marcas(sessao)
    carregar_itens(sessao)
    return sessao


def _item(sessao, slug) -> Item:
    return sessao.scalars(select(Item).where(Item.slug == slug)).one()


def test_carrega_os_47_itens_do_plano(catalogo):
    assert catalogo.scalar(select(func.count()).select_from(Item)) == 47


def test_itens_de_seguranca_marcados(catalogo):
    slugs = set(catalogo.scalars(select(Item.slug).where(Item.e_seguranca)).all())
    assert slugs == ITENS_DE_SEGURANCA


def test_body_tem_tamanhos_variantes_e_fases(catalogo):
    body = _item(catalogo, "body")

    assert {t.tamanho: t.quantidade_base for t in body.tamanhos} == {
        Tamanho.RN: 4, Tamanho.P: 8, Tamanho.M: 7, Tamanho.G: 6, Tamanho.GG: 6,
    }
    assert body.uso_clima == UsoClima.DIVIDE
    assert (body.variante_frio, body.variante_calor) == ("manga longa", "manga curta")
    assert body.escala_lavagem is True
    fases = {t.tamanho: t.fase_compra.codigo for t in body.tamanhos}
    assert fases[Tamanho.P] == "gestacao_7_8m"
    assert fases[Tamanho.GG] == "bebe_6_9m"


def test_regras_do_plano(catalogo):
    conforto = _item(catalogo, "bebe-conforto")
    regras = {(r.condicao, r.efeito): r.valor for r in conforto.regras}
    assert regras[(Condicao.SEM_CARRO, Efeito.MUDAR_PRIORIDADE)] == Prioridade.UTIL.value

    portao = _item(catalogo, "portao-seguranca")
    assert [(r.condicao, r.efeito) for r in portao.regras] == [
        (Condicao.CASA_COM_ESCADA, Efeito.INCLUIR_SO_SE)
    ]

    mosquiteiro = _item(catalogo, "mosquiteiro")
    assert (Condicao.PERFIL_QUENTE, Efeito.INCLUIR_SO_SE) in {
        (r.condicao, r.efeito) for r in mosquiteiro.regras
    }


def test_marcas_ligadas_com_faixa_e_nao_validadas(catalogo):
    berco = _item(catalogo, "berco")
    assert [v.marca.nome for v in berco.marcas][:2] == ["Tcil", "Reller"]
    assert all(v.faixa in Faixa for v in berco.marcas)
    assert catalogo.scalar(select(func.count()).select_from(Marca).where(Marca.validado)) == 0


def test_segunda_carga_nao_duplica_nem_sobrescreve(catalogo):
    berco = _item(catalogo, "berco")
    berco.nome = "Berço (editado no admin)"
    catalogo.flush()

    resumo = carregar_itens(catalogo)

    assert set(resumo.values()) == {0}
    assert _item(catalogo, "berco").nome == "Berço (editado no admin)"


def test_erro_de_digitacao_no_yaml_nomeia_o_item(sessao):
    carregar_base(sessao)
    carregar_marcas(sessao)
    dados = {
        "itens": [
            {
                "slug": "teste", "nome": "Teste", "categoria": "roupas",
                "fase": "gestacao_7_8m", "prioridade": "essencal",
                "quantidade": 1, "para_que_serve": "x", "como_escolher": "y",
            }
        ]
    }
    with pytest.raises(ValueError, match="item 'teste'.*essencal"):
        carregar_itens(sessao, dados)


def test_marca_desconhecida_e_recusada(sessao):
    carregar_base(sessao)
    carregar_marcas(sessao)
    dados = {
        "itens": [
            {
                "slug": "teste", "nome": "Teste", "categoria": "roupas",
                "fase": "gestacao_7_8m", "prioridade": "util", "quantidade": 1,
                "para_que_serve": "x", "como_escolher": "y", "marcas": ["Inexistente"],
            }
        ]
    }
    with pytest.raises(ValueError, match="item 'teste': marca 'Inexistente'"):
        carregar_itens(sessao, dados)


def test_item_sem_tamanhos_nem_quantidade_e_recusado(sessao):
    carregar_base(sessao)
    dados = {
        "itens": [
            {
                "slug": "teste", "nome": "Teste", "categoria": "roupas",
                "fase": "gestacao_7_8m", "prioridade": "util",
                "para_que_serve": "x", "como_escolher": "y",
            }
        ]
    }
    with pytest.raises(ValueError, match="item 'teste': informe 'tamanhos' ou 'quantidade'"):
        carregar_itens(sessao, dados)
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `docker compose run --rm api pytest tests/carga/test_itens.py`
Expected: FAIL com `ModuleNotFoundError: No module named 'seed.itens'`

- [ ] **Step 3: Implementar o carregador**

`api/seed/itens.py`:
```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.catalogo import (
    Categoria,
    FaseRoteiro,
    Item,
    ItemMarca,
    ItemRegra,
    ItemTamanho,
    Marca,
)
from app.db.enums import Condicao, Efeito, Faixa, Prioridade, Tamanho, UsoClima
from seed.util import buscar, enum_de, inserir_se_faltar, ler_yaml


def carregar_marcas(sessao: Session) -> int:
    linhas = [
        {"nome": m["nome"], "faixa_padrao": enum_de(Faixa, m["faixa"], f"marca '{m['nome']}'")}
        for m in ler_yaml("marcas.yaml")
    ]
    return inserir_se_faltar(sessao, Marca, linhas, ["nome"])


def carregar_itens(sessao: Session, dados: dict | None = None) -> dict[str, int]:
    """Cria os itens que ainda não existem. Item existente é ignorado (o admin manda)."""
    dados = dados if dados is not None else ler_yaml("itens.yaml")
    categorias = {c.slug: c.id for c in sessao.scalars(select(Categoria))}
    fases = {f.codigo: f.id for f in sessao.scalars(select(FaseRoteiro))}
    marcas = {m.nome: m for m in sessao.scalars(select(Marca))}
    existentes = set(sessao.scalars(select(Item.slug)))
    contagem = {"item": 0, "item_tamanho": 0, "item_regra": 0, "item_marca": 0}

    for ordem, bruto in enumerate(dados["itens"], start=1):
        slug = bruto["slug"]
        if slug in existentes:
            continue
        ctx = f"item '{slug}'"
        variantes = bruto.get("variantes", {})
        item = Item(
            slug=slug,
            nome=bruto["nome"],
            categoria_id=buscar(categorias, bruto["categoria"], ctx, "categoria"),
            fase_compra_id=buscar(fases, bruto["fase"], ctx, "fase"),
            prioridade_base=enum_de(Prioridade, bruto["prioridade"], ctx),
            e_seguranca=bruto.get("seguranca", False),
            uso_clima=enum_de(UsoClima, bruto.get("uso_clima", "neutro"), ctx),
            variante_frio=variantes.get("frio"),
            variante_calor=variantes.get("calor"),
            escala_lavagem=bruto.get("escala_lavagem", False),
            quantidade=bruto.get("quantidade"),
            unidade_texto=bruto.get("unidade"),
            idade_inicio_meses=bruto.get("idade_inicio_meses", 0),
            para_que_serve=bruto["para_que_serve"],
            como_escolher=bruto["como_escolher"],
            ordem=ordem,
        )

        fases_tamanho = bruto.get("fases_tamanho", {})
        for tamanho, quantidade in bruto.get("tamanhos", {}).items():
            fase = fases_tamanho.get(tamanho)
            item.tamanhos.append(
                ItemTamanho(
                    tamanho=enum_de(Tamanho, tamanho, ctx),
                    quantidade_base=quantidade,
                    fase_compra_id=buscar(fases, fase, ctx, "fase") if fase else None,
                )
            )
        if not item.tamanhos and item.quantidade is None:
            raise ValueError(f"{ctx}: informe 'tamanhos' ou 'quantidade'")

        for regra in bruto.get("regras", []):
            efeito = enum_de(Efeito, regra["efeito"], ctx)
            valor = regra.get("valor")
            if efeito == Efeito.MUDAR_PRIORIDADE:
                valor = enum_de(Prioridade, valor, ctx).value
            item.regras.append(
                ItemRegra(
                    condicao=enum_de(Condicao, regra["condicao"], ctx),
                    efeito=efeito,
                    valor=valor,
                )
            )

        for posicao, entrada in enumerate(bruto.get("marcas", []), start=1):
            nome, faixa = (
                (entrada, None) if isinstance(entrada, str)
                else (entrada["nome"], entrada.get("faixa"))
            )
            marca = buscar(marcas, nome, ctx, "marca")
            item.marcas.append(
                ItemMarca(
                    marca=marca,
                    faixa=enum_de(Faixa, faixa, ctx) if faixa else marca.faixa_padrao,
                    ordem=posicao,
                )
            )

        sessao.add(item)
        contagem["item"] += 1
        contagem["item_tamanho"] += len(item.tamanhos)
        contagem["item_regra"] += len(item.regras)
        contagem["item_marca"] += len(item.marcas)

    sessao.flush()
    return contagem
```

`api/seed/dados/marcas.yaml` (faixas são estimativa inicial, a validar):
```yaml
# Roupas
- {nome: Hering Kids, faixa: intermediario}
- {nome: Carter's, faixa: investir}
- {nome: Tip Top, faixa: intermediario}
- {nome: Up Baby, faixa: intermediario}
- {nome: Brandili, faixa: economico}
- {nome: C&A, faixa: economico}
- {nome: Renner, faixa: economico}
- {nome: Riachuelo, faixa: economico}
# Móveis, sono e passeio
- {nome: Tcil, faixa: intermediario}
- {nome: Reller, faixa: intermediario}
- {nome: Matic, faixa: investir}
- {nome: Burigotto, faixa: economico}
- {nome: Galzerano, faixa: economico}
- {nome: Ortobom, faixa: intermediario}
- {nome: Castor, faixa: intermediario}
- {nome: Fom, faixa: economico}
- {nome: Papi, faixa: intermediario}
- {nome: Hering, faixa: intermediario}
- {nome: Motorola, faixa: intermediario}
- {nome: Philips Avent, faixa: investir}
- {nome: Multikids Baby, faixa: economico}
- {nome: Maxi-Cosi, faixa: investir}
- {nome: Cybex, faixa: investir}
- {nome: Chicco, faixa: intermediario}
- {nome: Infanti, faixa: economico}
- {nome: ABC Design, faixa: investir}
- {nome: Ergobaby, faixa: investir}
- {nome: Masterbag, faixa: intermediario}
- {nome: Safety 1st, faixa: intermediario}
# Higiene e saúde
- {nome: Pampers, faixa: investir}
- {nome: Huggies, faixa: intermediario}
- {nome: MamyPoko, faixa: intermediario}
- {nome: Turma da Mônica Baby, faixa: economico}
- {nome: Personal Baby, faixa: economico}
- {nome: Cremer, faixa: economico}
- {nome: Bepantol Baby, faixa: intermediario}
- {nome: Hipoglós, faixa: economico}
- {nome: Desitin, faixa: investir}
- {nome: Johnson's Baby, faixa: economico}
- {nome: Granado Bebê, faixa: intermediario}
- {nome: Mustela, faixa: investir}
- {nome: Dove Baby, faixa: intermediario}
- {nome: Natura Mamãe e Bebê, faixa: intermediario}
- {nome: G-Tech, faixa: economico}
- {nome: Omron, faixa: investir}
- {nome: Lillo, faixa: economico}
- {nome: Kuka, faixa: economico}
- {nome: NoseFrida, faixa: investir}
# Alimentação
- {nome: Medela, faixa: investir}
- {nome: MAM, faixa: intermediario}
- {nome: NUK, faixa: intermediario}
- {nome: Buba, faixa: economico}
# Para a mãe
- {nome: Intimus, faixa: economico}
- {nome: Always, faixa: economico}
- {nome: Lansinoh, faixa: investir}
# Genéricos
- {nome: Linhas de loja, faixa: economico}
- {nome: Linhas de farmácia, faixa: economico}
```

`api/seed/dados/itens.yaml`:
```yaml
padroes:
  fases_roupa: &fases_roupa
    RN: gestacao_7_8m
    P: gestacao_7_8m
    M: bebe_0_3m
    G: bebe_3_6m
    GG: bebe_6_9m
  marcas_roupa: &marcas_roupa [Hering Kids, Carter's, Tip Top, Up Baby, Brandili, C&A, Renner, Riachuelo]
  como_escolher_roupa: &como_roupa Algodão, botões ou zíper na frente, sem laços, fitas ou peças soltas.

itens:
  # ---------- Roupas ----------
  - slug: body
    nome: Body
    categoria: roupas
    fase: gestacao_7_8m
    prioridade: essencial
    uso_clima: divide
    variantes: {frio: manga longa, calor: manga curta}
    escala_lavagem: true
    tamanhos: {RN: 4, P: 8, M: 7, G: 6, GG: 6}
    fases_tamanho: *fases_roupa
    para_que_serve: Peça básica do dia a dia, sozinha no calor ou por baixo no frio.
    como_escolher: *como_roupa
    marcas: *marcas_roupa
  - slug: calca-mijao
    nome: Calça ou mijão
    categoria: roupas
    fase: gestacao_7_8m
    prioridade: essencial
    uso_clima: divide
    variantes: {frio: comprida, calor: curta}
    escala_lavagem: true
    tamanhos: {RN: 3, P: 6, M: 5, G: 5, GG: 5}
    fases_tamanho: *fases_roupa
    para_que_serve: Completa o body; com pé, dispensa a meia nos primeiros meses.
    como_escolher: *como_roupa
    marcas: *marcas_roupa
  - slug: macacao
    nome: Macacão
    categoria: roupas
    fase: gestacao_7_8m
    prioridade: essencial
    uso_clima: divide
    variantes: {frio: longo com pé, calor: curto}
    escala_lavagem: true
    tamanhos: {RN: 2, P: 4, M: 4, G: 3, GG: 3}
    fases_tamanho: *fases_roupa
    para_que_serve: Peça única, prática para dormir e sair.
    como_escolher: *como_roupa
    marcas: *marcas_roupa
  - slug: casaquinho
    nome: Casaquinho
    categoria: roupas
    fase: gestacao_7_8m
    prioridade: util
    escala_lavagem: true
    tamanhos: {RN: 1, P: 2, M: 2, G: 2, GG: 2}
    fases_tamanho: *fases_roupa
    para_que_serve: Uma camada a mais para noites frescas e ambientes com ar-condicionado.
    como_escolher: *como_roupa
    marcas: *marcas_roupa
  - slug: meias
    nome: Meias (pares)
    categoria: roupas
    fase: gestacao_7_8m
    prioridade: essencial
    escala_lavagem: true
    tamanhos: {RN: 3, P: 6, M: 5, G: 4, GG: 4}
    fases_tamanho: *fases_roupa
    para_que_serve: Manter os pés aquecidos quando a roupa não tem pé.
    como_escolher: Algodão, punho macio que não aperta e sola antiderrapante quando o bebê começar a ficar em pé.
    marcas: *marcas_roupa
  - slug: gorro
    nome: Gorro
    categoria: roupas
    fase: gestacao_7_8m
    prioridade: util
    uso_clima: so_frio
    tamanhos: {RN: 1, P: 2, M: 1, G: 1, GG: 1}
    fases_tamanho: *fases_roupa
    para_que_serve: Proteger a cabeça em passeios nos meses frios.
    como_escolher: Malha macia, sem pompom solto nem cordão de amarrar. Não usar para dormir.
    marcas: *marcas_roupa
  - slug: manta
    nome: Manta
    categoria: roupas
    fase: gestacao_7_8m
    prioridade: essencial
    quantidade: 2
    unidade: mantas
    para_que_serve: Envolver o bebê no colo, no carrinho e nas saídas.
    como_escolher: Leve no calor, mais grossa no frio. Nunca solta dentro do berço na hora de dormir.
    marcas: [Linhas de loja]
  - slug: toalha-capuz
    nome: Toalha com capuz
    categoria: roupas
    fase: gestacao_7_8m
    prioridade: essencial
    escala_lavagem: true
    quantidade: 3
    unidade: toalhas
    para_que_serve: Secar o bebê depois do banho, cobrindo a cabeça.
    como_escolher: Algodão macio e absorvente, que seque rápido.
    marcas: [Linhas de loja]
  - slug: fralda-pano
    nome: Fraldas de pano ou paninhos de boca
    categoria: roupas
    fase: gestacao_7_8m
    prioridade: essencial
    escala_lavagem: true
    quantidade: 10
    unidade: unidades
    para_que_serve: Limpar regurgitação, proteger o ombro e forrar o trocador.
    como_escolher: Algodão, com bainha bem costurada.
    marcas: [Linhas de loja]
  - slug: saco-dormir
    nome: Saco de dormir
    categoria: roupas
    fase: gestacao_7_8m
    prioridade: util
    uso_clima: so_frio
    quantidade: 2
    unidade: sacos de dormir
    para_que_serve: Aquecer à noite sem cobertor solto no berço.
    como_escolher: Do tamanho do bebê, sem capuz, com cava que não deixe a cabeça escorregar para dentro.
    marcas: [Linhas de loja]

  # ---------- Sono e quarto ----------
  - slug: berco
    nome: Berço
    categoria: sono-e-quarto
    fase: gestacao_5_7m
    prioridade: essencial
    seguranca: true
    quantidade: 1
    unidade: berço
    para_que_serve: Lugar seguro de sono desde o primeiro dia.
    como_escolher: Selo INMETRO, vão entre as grades de no máximo 6,5 cm e estrado com regulagem de altura.
    regras:
      - {condicao: apartamento, efeito: dica, valor: Em apartamento pequeno, um berço compacto ou mini berço com selo INMETRO ocupa menos espaço.}
    marcas: [Tcil, Reller, Matic, Burigotto, Galzerano]
  - slug: colchao-berco
    nome: Colchão de berço
    categoria: sono-e-quarto
    fase: gestacao_5_7m
    prioridade: essencial
    seguranca: true
    quantidade: 1
    unidade: colchão
    para_que_serve: Base firme para o bebê dormir.
    como_escolher: Firme e do tamanho exato do berço, sem vão nas laterais.
    marcas: [Ortobom, Castor, Fom]
  - slug: lencol-elastico
    nome: Lençol com elástico
    categoria: sono-e-quarto
    fase: gestacao_7_8m
    prioridade: essencial
    seguranca: true
    escala_lavagem: true
    quantidade: 4
    unidade: lençóis
    para_que_serve: Forrar o colchão.
    como_escolher: Bem justo no colchão. No berço, nada de edredom, travesseiro ou protetor de grade.
    marcas: [Papi, Hering, Linhas de loja]
  - slug: comoda-trocador
    nome: Cômoda com trocador
    categoria: sono-e-quarto
    fase: gestacao_5_7m
    prioridade: util
    quantidade: 1
    unidade: cômoda
    para_que_serve: Guardar as roupas e trocar a fralda na altura certa.
    como_escolher: Trocador com bordas elevadas e cômoda fixada na parede.
    regras:
      - {condicao: apartamento, efeito: dica, valor: Em apartamento pequeno, a cômoda com trocador economiza espaço e dispensa um trocador separado.}
    marcas: [Tcil, Reller, Matic]
  - slug: baba-eletronica
    nome: Babá eletrônica
    categoria: sono-e-quarto
    fase: gestacao_7_8m
    prioridade: util
    quantidade: 1
    unidade: aparelho
    para_que_serve: Ouvir ou ver o bebê de outro cômodo.
    como_escolher: Alcance suficiente para a casa e fio sempre longe do berço.
    marcas: [Motorola, Philips Avent, Multikids Baby]
  - slug: mosquiteiro
    nome: Mosquiteiro
    categoria: sono-e-quarto
    fase: gestacao_7_8m
    prioridade: util
    quantidade: 1
    unidade: mosquiteiro
    para_que_serve: Proteger o bebê de insetos.
    como_escolher: Bem preso por fora, sem sobras de tecido dentro do berço.
    regras:
      - {condicao: perfil_quente, efeito: incluir_so_se}
    marcas: [Linhas de loja]

  # ---------- Higiene e banho ----------
  - slug: fraldas-descartaveis
    nome: Fraldas descartáveis
    categoria: higiene-e-banho
    fase: gestacao_7_8m
    prioridade: essencial
    quantidade: 2
    unidade: pacotes RN; depois, cerca de 1 mês de estoque de P
    para_que_serve: Uso diário; no começo são de 8 a 12 trocas por dia.
    como_escolher: Pouco tamanho RN, que dura pouco. Testar marcas antes de fazer estoque.
    marcas: [Pampers, Huggies, MamyPoko, Turma da Mônica Baby, Personal Baby]
  - slug: algodao-lenco
    nome: Algodão e lenço umedecido
    categoria: higiene-e-banho
    fase: gestacao_7_8m
    prioridade: essencial
    quantidade: 6
    unidade: pacotes (4 de algodão e 2 de lenço)
    para_que_serve: Limpeza na troca de fralda.
    como_escolher: Nas primeiras semanas, algodão com água. Lenço sem perfume e sem álcool.
    marcas: [Cremer, Huggies, Pampers]
  - slug: pomada-assadura
    nome: Pomada para assadura
    categoria: higiene-e-banho
    fase: gestacao_7_8m
    prioridade: essencial
    quantidade: 2
    unidade: tubos
    para_que_serve: Prevenir e tratar assaduras.
    como_escolher: Com óxido de zinco ou dexpantenol; confirme com o pediatra.
    marcas: [Bepantol Baby, Hipoglós, Desitin]
  - slug: sabonete-xampu
    nome: Sabonete e xampu de bebê
    categoria: higiene-e-banho
    fase: gestacao_7_8m
    prioridade: essencial
    quantidade: 2
    unidade: frascos (1 de cada)
    para_que_serve: Banho.
    como_escolher: pH neutro e sem perfume forte.
    marcas: [Johnson's Baby, Granado Bebê, Mustela, Dove Baby, Natura Mamãe e Bebê]
  - slug: banheira
    nome: Banheira com suporte
    categoria: higiene-e-banho
    fase: gestacao_7_8m
    prioridade: essencial
    quantidade: 1
    unidade: banheira
    para_que_serve: Banho seguro na altura certa para quem dá o banho.
    como_escolher: Estável e com apoio anatômico; o balde de banho é uma alternativa.
    marcas: [Burigotto, Safety 1st]
  - slug: termometro
    nome: Termômetro corporal digital
    categoria: higiene-e-banho
    fase: gestacao_7_8m
    prioridade: essencial
    seguranca: true
    quantidade: 1
    unidade: termômetro
    para_que_serve: Medir a febre.
    como_escolher: Digital; nunca de mercúrio.
    marcas: [G-Tech, Omron]
  - slug: kit-unha
    nome: Kit unha e escova macia
    categoria: higiene-e-banho
    fase: gestacao_7_8m
    prioridade: util
    quantidade: 1
    unidade: kit
    para_que_serve: Cortar as unhas e pentear.
    como_escolher: Tesoura de ponta redonda ou lixa de bebê.
    marcas: [Lillo, Kuka]
  - slug: aspirador-nasal
    nome: Aspirador nasal e soro fisiológico
    categoria: higiene-e-banho
    fase: gestacao_7_8m
    prioridade: util
    quantidade: 1
    unidade: kit
    para_que_serve: Desentupir o nariz.
    como_escolher: Fácil de desmontar e lavar.
    marcas: [NoseFrida, Lillo]

  # ---------- Passeio e transporte ----------
  - slug: bebe-conforto
    nome: Bebê conforto
    categoria: passeio-e-transporte
    fase: gestacao_5_7m
    prioridade: essencial
    seguranca: true
    quantidade: 1
    unidade: bebê conforto
    para_que_serve: Transporte no carro, obrigatório por lei desde a saída da maternidade.
    como_escolher: Selo INMETRO, instalado voltado para trás; teste no carro antes. Evite usado sem histórico.
    regras:
      - {condicao: sem_carro, efeito: mudar_prioridade, valor: util}
      - {condicao: sem_carro, efeito: dica, valor: Mesmo sem carro, ele continua necessário para táxi, carro de aplicativo ou carona.}
    marcas: [Maxi-Cosi, Cybex, Chicco, Burigotto, Safety 1st, Infanti]
  - slug: carrinho
    nome: Carrinho
    categoria: passeio-e-transporte
    fase: gestacao_5_7m
    prioridade: essencial
    quantidade: 1
    unidade: carrinho
    para_que_serve: Passeios do dia a dia.
    como_escolher: Encosto que deita totalmente, cinto de 5 pontos e que caiba no porta-malas.
    regras:
      - {condicao: sem_carro, efeito: dica, valor: Sem carro, prefira um carrinho leve e fácil de fechar para ônibus e metrô.}
    marcas: [Burigotto, Galzerano, Chicco, ABC Design, Cybex]
  - slug: sling
    nome: Sling ou canguru
    categoria: passeio-e-transporte
    fase: bebe_0_3m
    prioridade: util
    quantidade: 1
    unidade: sling ou canguru
    para_que_serve: Carregar o bebê com as mãos livres.
    como_escolher: Posição em M (joelhos acima do bumbum) e rosto sempre visível.
    regras:
      - {condicao: sem_carro, efeito: mudar_prioridade, valor: essencial}
    marcas: [Ergobaby, Infanti, Chicco]
  - slug: bolsa-maternidade
    nome: Bolsa maternidade e trocador portátil
    categoria: passeio-e-transporte
    fase: gestacao_7_8m
    prioridade: essencial
    quantidade: 1
    unidade: bolsa
    para_que_serve: Levar o necessário nas saídas.
    como_escolher: Bolsos separados e trocador lavável.
    marcas: [Masterbag, Linhas de loja]

  # ---------- Alimentação ----------
  - slug: almofada-amamentacao
    nome: Almofada de amamentação
    categoria: alimentacao
    fase: gestacao_7_8m
    prioridade: util
    quantidade: 1
    unidade: almofada
    para_que_serve: Apoiar o bebê e a coluna de quem amamenta.
    como_escolher: Capa removível. Nunca usar para o bebê dormir.
    marcas: [Linhas de loja]
  - slug: bomba-tira-leite
    nome: Bomba tira-leite
    categoria: alimentacao
    fase: bebe_0_3m
    prioridade: pode_esperar
    quantidade: 1
    unidade: bomba
    para_que_serve: Tirar e guardar leite.
    como_escolher: Só se precisar; a manual basta para uso ocasional.
    marcas: [Medela, Philips Avent]
  - slug: mamadeira
    nome: Mamadeira
    categoria: alimentacao
    fase: bebe_0_3m
    prioridade: pode_esperar
    quantidade: 2
    unidade: mamadeiras
    para_que_serve: Oferecer leite tirado ou fórmula.
    como_escolher: Livre de BPA; só comprar se houver indicação.
    marcas: [Philips Avent, MAM, NUK, Lillo, Kuka]
  - slug: cadeira-alimentacao
    nome: Cadeira de alimentação
    categoria: alimentacao
    fase: bebe_3_6m
    prioridade: essencial
    idade_inicio_meses: 6
    quantidade: 1
    unidade: cadeira
    para_que_serve: Comer sentado e seguro.
    como_escolher: Cinto de 5 pontos, base larga e bandeja lavável.
    marcas: [Burigotto, Chicco, Safety 1st, Galzerano]
  - slug: kit-introducao
    nome: Pratos, colheres e babadores
    categoria: alimentacao
    fase: bebe_3_6m
    prioridade: essencial
    idade_inicio_meses: 6
    quantidade: 9
    unidade: peças (2 pratos, 3 colheres e 4 babadores)
    para_que_serve: Introdução alimentar.
    como_escolher: Silicone ou plástico livre de BPA e colher macia.
    marcas: [MAM, NUK, Buba, Lillo]
  - slug: copo-transicao
    nome: Copo de transição
    categoria: alimentacao
    fase: bebe_6_9m
    prioridade: essencial
    idade_inicio_meses: 6
    quantidade: 1
    unidade: copo
    para_que_serve: Oferecer água a partir dos 6 meses.
    como_escolher: Com alça e bico macio, ou borda 360.
    marcas: [NUK, MAM, Lillo]

  # ---------- Segurança da casa ----------
  - slug: protetor-tomada
    nome: Protetor de tomada
    categoria: seguranca-da-casa
    fase: bebe_6_9m
    prioridade: essencial
    seguranca: true
    idade_inicio_meses: 6
    quantidade: 6
    unidade: protetores (um por tomada baixa)
    para_que_serve: Evitar choque elétrico.
    como_escolher: Difícil de a criança remover.
    marcas: [Safety 1st, Multikids Baby]
  - slug: trava-gaveta
    nome: Trava de gaveta e armário
    categoria: seguranca-da-casa
    fase: bebe_6_9m
    prioridade: essencial
    seguranca: true
    idade_inicio_meses: 6
    quantidade: 8
    unidade: travas (de 6 a 10)
    para_que_serve: Afastar produtos de limpeza e objetos cortantes.
    como_escolher: Adesiva ou magnética.
    marcas: [Safety 1st, Multikids Baby]
  - slug: portao-seguranca
    nome: Portão de segurança
    categoria: seguranca-da-casa
    fase: bebe_6_9m
    prioridade: essencial
    seguranca: true
    idade_inicio_meses: 6
    quantidade: 1
    unidade: portão por acesso de escada
    para_que_serve: Bloquear a escada e a cozinha.
    como_escolher: No topo da escada, sempre parafusado (nunca só de pressão).
    regras:
      - {condicao: casa_com_escada, efeito: incluir_so_se}
    marcas: [Safety 1st, Burigotto]
  - slug: protetor-quina
    nome: Protetor de quina
    categoria: seguranca-da-casa
    fase: bebe_9_12m
    prioridade: util
    seguranca: true
    idade_inicio_meses: 9
    quantidade: 1
    unidade: kit
    para_que_serve: Amortecer batidas.
    como_escolher: Silicone bem aderido.
    marcas: [Safety 1st, Multikids Baby]

  # ---------- Para a mãe ----------
  - slug: absorvente-pos-parto
    nome: Absorvente pós-parto
    categoria: para-a-mae
    fase: gestacao_7_8m
    prioridade: essencial
    quantidade: 3
    unidade: pacotes (2 a 3)
    para_que_serve: Sangramento das primeiras semanas.
    como_escolher: Noturno, de fluxo intenso e sem perfume.
    marcas: [Intimus, Always, Linhas de farmácia]
  - slug: calcinha-pos-parto
    nome: Calcinha pós-parto
    categoria: para-a-mae
    fase: gestacao_7_8m
    prioridade: essencial
    quantidade: 5
    unidade: calcinhas
    para_que_serve: Conforto e apoio para o absorvente.
    como_escolher: Cintura alta e algodão.
    marcas: [Linhas de loja]
  - slug: sutia-amamentacao
    nome: Sutiã de amamentação
    categoria: para-a-mae
    fase: gestacao_7_8m
    prioridade: essencial
    quantidade: 3
    unidade: sutiãs
    para_que_serve: Amamentar sem tirar a peça.
    como_escolher: Comprar perto do parto, um número acima e sem aro.
    marcas: [Linhas de loja]
  - slug: protetor-seios
    nome: Protetor de seios
    categoria: para-a-mae
    fase: gestacao_7_8m
    prioridade: util
    quantidade: 1
    unidade: caixa (ou 3 pares laváveis)
    para_que_serve: Absorver o vazamento de leite.
    como_escolher: Trocar sempre que estiver úmido.
    marcas: [Lansinoh, Philips Avent, Lillo]
  - slug: pomada-mamilo
    nome: Pomada para mamilo
    categoria: para-a-mae
    fase: gestacao_7_8m
    prioridade: util
    quantidade: 1
    unidade: tubo
    para_que_serve: Aliviar fissuras.
    como_escolher: Lanolina pura; confirme com quem acompanha a amamentação.
    marcas: [Lansinoh, Medela]
  - slug: camisola-abertura
    nome: Camisola ou pijama com abertura
    categoria: para-a-mae
    fase: gestacao_7_8m
    prioridade: essencial
    quantidade: 3
    unidade: peças
    para_que_serve: Amamentar na maternidade e em casa.
    como_escolher: Botões na frente.
    marcas: [Linhas de loja]
  - slug: chinelo-banho
    nome: Chinelo e itens de banho
    categoria: para-a-mae
    fase: gestacao_7_8m
    prioridade: essencial
    quantidade: 1
    unidade: kit
    para_que_serve: Mala da maternidade.
    como_escolher: Chinelo antiderrapante.
  - slug: garrafa-agua
    nome: Garrafa de água grande
    categoria: para-a-mae
    fase: gestacao_7_8m
    prioridade: util
    quantidade: 1
    unidade: garrafa
    para_que_serve: Hidratação durante a amamentação.
    como_escolher: Com canudo, para usar com uma mão só.
  - slug: cinta-pos-parto
    nome: Cinta pós-parto
    categoria: para-a-mae
    fase: bebe_0_3m
    prioridade: pode_esperar
    quantidade: 1
    unidade: cinta
    para_que_serve: Apoio abdominal depois do parto.
    como_escolher: Só se o médico indicar.
    marcas: [Linhas de farmácia]
```

- [ ] **Step 4: Rodar e ver passar**

Run: `docker compose run --rm api pytest tests/carga`
Expected: `13 passed` (4 da Task 5 + 9 novos; 26 no total). Se o total de itens não for 47, compare o YAML com o plano: 10 roupas, 6 sono, 8 higiene, 4 passeio, 6 alimentação, 4 casa, 9 mãe.

- [ ] **Step 5: Commit**

```bash
git add api/seed api/tests/carga
git commit -m "feat: seed de marcas e dos 47 itens do plano

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: Seed — municípios do IBGE e exceções de clima

**Files:**
- Create: `api/seed/baixar_municipios.py`, `api/seed/cidades.py`, `api/seed/dados/municipios.csv` (gerado), `api/seed/dados/excecoes_municipios.yaml`
- Test: `api/tests/carga/test_cidades.py`

**Interfaces:**
- Consumes: `carregar_base` (estados), utilitários (Task 5), `Municipio`.
- Produces: `seed.cidades.normalizar_busca(texto: str) -> str` (sem acento, minúsculas, espaços simples; **a API da Etapa 3 usa a mesma função na busca**), `seed.cidades.carregar_municipios(sessao) -> int`, `seed.cidades.aplicar_excecoes(sessao, dados: list | None = None) -> int`.

- [ ] **Step 1: Baixar a lista oficial de municípios**

`api/seed/baixar_municipios.py`:
```python
"""Baixa a lista oficial de municípios do IBGE para dados/municipios.csv.

Uso único (o CSV vai para o git): docker compose run --rm api python -m seed.baixar_municipios
"""
import csv
import json
import urllib.request

from seed.util import PASTA_DADOS

URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios?view=nivelado"


def main() -> None:
    with urllib.request.urlopen(URL, timeout=60) as resposta:
        dados = json.load(resposta)
    linhas = sorted(
        (int(m["municipio-id"]), m["municipio-nome"], m["UF-sigla"]) for m in dados
    )
    with open(PASTA_DADOS / "municipios.csv", "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["codigo_ibge", "nome", "uf"])
        escritor.writerows(linhas)
    print(f"{len(linhas)} municípios gravados")


if __name__ == "__main__":
    main()
```

Run: `docker compose run --rm api python -m seed.baixar_municipios`
Expected: `5571 municípios gravados` (ou um número muito próximo; o IBGE conta 5.570 municípios mais o Distrito Federal). Abra `api/seed/dados/municipios.csv` e confira a primeira linha (`codigo_ibge,nome,uf`) e uma linha conhecida, como `4106902,Curitiba,PR`. Se o comando der `KeyError`, imprima `dados[0]` para ver os nomes dos campos e ajuste as três chaves.

- [ ] **Step 2: Escrever os testes que falham**

`api/tests/carga/test_cidades.py`:
```python
import pytest
from sqlalchemy import func, select

from app.db.catalogo import Municipio
from app.db.enums import PerfilCodigo
from seed.base import carregar_base
from seed.cidades import aplicar_excecoes, carregar_municipios, normalizar_busca


@pytest.fixture
def cidades(sessao):
    carregar_base(sessao)
    carregar_municipios(sessao)
    aplicar_excecoes(sessao)
    return sessao


def _municipio(sessao, nome, uf) -> Municipio:
    return sessao.scalars(
        select(Municipio).where(Municipio.nome == nome, Municipio.uf == uf)
    ).one()


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("São João d'Aliança", "sao joao d'alianca"),
        ("  Florianópolis ", "florianopolis"),
        ("SAO   PAULO", "sao paulo"),
    ],
)
def test_normalizar_busca(entrada, esperado):
    assert normalizar_busca(entrada) == esperado


def test_carrega_todos_os_municipios(cidades):
    total = cidades.scalar(select(func.count()).select_from(Municipio))
    assert 5560 <= total <= 5600
    assert _municipio(cidades, "São Paulo", "SP").nome_busca == "sao paulo"


def test_excecoes_de_serra(cidades):
    assert _municipio(cidades, "Campos do Jordão", "SP").perfil_excecao == PerfilCodigo.FRIO
    assert _municipio(cidades, "Garanhuns", "PE").perfil_excecao == PerfilCodigo.MODERADO
    assert _municipio(cidades, "Curitiba", "PR").perfil_excecao is None


def test_excecao_acerta_so_a_uf_informada(cidades):
    homonimos = cidades.scalars(
        select(Municipio).where(Municipio.nome_busca == "bom jesus")
    ).all()
    assert len(homonimos) > 1

    aplicar_excecoes(cidades, [{"nome": "Bom Jesus", "uf": "RS", "perfil": "frio"}])

    marcados = {m.uf for m in homonimos if m.perfil_excecao is not None}
    assert marcados == {"RS"}


def test_excecao_de_municipio_inexistente_e_recusada(cidades):
    with pytest.raises(ValueError, match="Cidade Inventada/SP.*não encontrado"):
        aplicar_excecoes(cidades, [{"nome": "Cidade Inventada", "uf": "SP", "perfil": "frio"}])


def test_carga_de_municipios_e_idempotente(cidades):
    assert carregar_municipios(cidades) == 0
```

- [ ] **Step 3: Rodar e ver falhar**

Run: `docker compose run --rm api pytest tests/carga/test_cidades.py`
Expected: FAIL com `ModuleNotFoundError: No module named 'seed.cidades'`

- [ ] **Step 4: Implementar**

`api/seed/cidades.py`:
```python
import csv
import unicodedata

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.catalogo import Municipio
from app.db.enums import PerfilCodigo
from seed.util import PASTA_DADOS, enum_de, inserir_se_faltar, ler_yaml

TAMANHO_LOTE = 1000


def normalizar_busca(texto: str) -> str:
    """Minúsculas, sem acento e com espaços simples: 'São  Paulo' -> 'sao paulo'."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return " ".join(sem_acento.lower().split())


def carregar_municipios(sessao: Session) -> int:
    with open(PASTA_DADOS / "municipios.csv", encoding="utf-8", newline="") as arquivo:
        linhas = [
            {
                "codigo_ibge": int(linha["codigo_ibge"]),
                "nome": linha["nome"],
                "nome_busca": normalizar_busca(linha["nome"]),
                "uf": linha["uf"],
            }
            for linha in csv.DictReader(arquivo)
        ]
    return sum(
        inserir_se_faltar(sessao, Municipio, linhas[i : i + TAMANHO_LOTE], ["codigo_ibge"])
        for i in range(0, len(linhas), TAMANHO_LOTE)
    )


def aplicar_excecoes(sessao: Session, dados: list | None = None) -> int:
    """Marca o perfil de exceção, sem mexer em município já marcado (pelo admin)."""
    dados = dados if dados is not None else ler_yaml("excecoes_municipios.yaml")
    aplicadas = 0
    for bruto in dados:
        ctx = f"exceção '{bruto['nome']}/{bruto['uf']}'"
        municipio = sessao.scalars(
            select(Municipio).where(
                Municipio.nome_busca == normalizar_busca(bruto["nome"]),
                Municipio.uf == bruto["uf"],
            )
        ).one_or_none()
        if municipio is None:
            raise ValueError(f"{ctx}: município não encontrado")
        if municipio.perfil_excecao is None:
            municipio.perfil_excecao = enum_de(PerfilCodigo, bruto["perfil"], ctx)
            aplicadas += 1
    sessao.flush()
    return aplicadas
```

`api/seed/dados/excecoes_municipios.yaml` (cidades cujo clima foge do padrão do estado; a validar):
```yaml
# Serra fluminense
- {nome: Petrópolis, uf: RJ, perfil: frio}
- {nome: Teresópolis, uf: RJ, perfil: frio}
- {nome: Nova Friburgo, uf: RJ, perfil: frio}
# Serra da Mantiqueira e sul de Minas
- {nome: Campos do Jordão, uf: SP, perfil: frio}
- {nome: Camanducaia, uf: MG, perfil: frio}
- {nome: Gonçalves, uf: MG, perfil: frio}
- {nome: Maria da Fé, uf: MG, perfil: frio}
- {nome: Poços de Caldas, uf: MG, perfil: frio}
- {nome: Barbacena, uf: MG, perfil: frio}
# Serras do Nordeste
- {nome: Garanhuns, uf: PE, perfil: moderado}
- {nome: Triunfo, uf: PE, perfil: moderado}
- {nome: Vitória da Conquista, uf: BA, perfil: moderado}
- {nome: Guaramiranga, uf: CE, perfil: moderado}
# Região serrana do Espírito Santo
- {nome: Domingos Martins, uf: ES, perfil: moderado}
- {nome: Venda Nova do Imigrante, uf: ES, perfil: moderado}
# Norte e oeste do Paraná
- {nome: Londrina, uf: PR, perfil: moderado}
- {nome: Maringá, uf: PR, perfil: moderado}
- {nome: Foz do Iguaçu, uf: PR, perfil: moderado}
```

- [ ] **Step 5: Rodar e ver passar**

Run: `docker compose run --rm api pytest tests/carga`
Expected: `21 passed` (13 + 8 novos; 34 no total)

- [ ] **Step 6: Commit**

```bash
git add api/seed api/tests/carga
git commit -m "feat: seed de municípios do IBGE com exceções de clima

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Seed — regras de segurança e comando `python -m seed`

**Files:**
- Create: `api/seed/seguranca.py`, `api/seed/carregar.py`, `api/seed/__main__.py`, `api/seed/dados/seguranca.yaml`
- Modify: `README.md`
- Test: `api/tests/carga/test_carregar.py`

**Interfaces:**
- Consumes: tudo das Tasks 5–7.
- Produces: `seed.seguranca.carregar_seguranca(sessao) -> dict[str, int]` (chave `regra_seguranca`), `seed.carregar.carregar_tudo(sessao) -> dict[str, int]` (junta todos os resumos, mais `marca`, `municipio`, `municipio_excecao`), comando `python -m seed`.

- [ ] **Step 1: Escrever os testes que falham**

`api/tests/carga/test_carregar.py`:
```python
from sqlalchemy import select

from app.db.catalogo import Item, Marca, RegraSeguranca
from app.db.enums import TemaSeguranca
from seed.carregar import carregar_tudo


def test_carga_completa_e_idempotente(sessao):
    primeira = carregar_tudo(sessao)
    segunda = carregar_tudo(sessao)

    assert primeira["item"] == 47
    assert primeira["regra_seguranca"] == 8
    assert set(segunda.values()) == {0}


def test_regras_de_seguranca_ligadas_aos_itens(sessao):
    carregar_tudo(sessao)

    sono = sessao.scalars(
        select(RegraSeguranca).where(RegraSeguranca.codigo == "sono-seguro")
    ).one()
    assert sono.tema == TemaSeguranca.SONO
    assert sono.validado is False
    assert "berco" in {i.slug for i in sono.itens}

    conforto = sessao.scalars(select(Item).where(Item.slug == "bebe-conforto")).one()
    assert "transporte-bebe-conforto" in {r.codigo for r in conforto.regras_seguranca}


def test_recarga_preserva_edicao_feita_no_admin(sessao):
    carregar_tudo(sessao)
    marca = sessao.scalars(select(Marca).where(Marca.nome == "Tcil")).one()
    marca.validado = True
    marca.fonte = "site oficial, conferido"
    sessao.flush()

    carregar_tudo(sessao)
    sessao.expire_all()

    marca = sessao.scalars(select(Marca).where(Marca.nome == "Tcil")).one()
    assert marca.validado is True
    assert marca.fonte == "site oficial, conferido"
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `docker compose run --rm api pytest tests/carga/test_carregar.py`
Expected: FAIL com `ModuleNotFoundError: No module named 'seed.carregar'`

- [ ] **Step 3: Implementar**

`api/seed/seguranca.py`:
```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.catalogo import Item, RegraSeguranca
from app.db.enums import TemaSeguranca
from seed.util import buscar, enum_de, ler_yaml


def carregar_seguranca(sessao: Session) -> dict[str, int]:
    itens = {i.slug: i for i in sessao.scalars(select(Item))}
    existentes = set(sessao.scalars(select(RegraSeguranca.codigo)))
    novas = 0
    for bruto in ler_yaml("seguranca.yaml"):
        codigo = bruto["codigo"]
        if codigo in existentes:
            continue
        ctx = f"regra '{codigo}'"
        sessao.add(
            RegraSeguranca(
                codigo=codigo,
                tema=enum_de(TemaSeguranca, bruto["tema"], ctx),
                idade_inicio_meses=bruto["idade_inicio_meses"],
                idade_fim_meses=bruto["idade_fim_meses"],
                texto=bruto["texto"],
                base=bruto["base"],
                itens=[buscar(itens, slug, ctx, "item") for slug in bruto.get("itens", [])],
            )
        )
        novas += 1
    sessao.flush()
    return {"regra_seguranca": novas}
```

`api/seed/carregar.py`:
```python
from sqlalchemy.orm import Session

from seed.base import carregar_base
from seed.cidades import aplicar_excecoes, carregar_municipios
from seed.itens import carregar_itens, carregar_marcas
from seed.seguranca import carregar_seguranca


def carregar_tudo(sessao: Session) -> dict[str, int]:
    """Carrega todo o conteúdo na ordem das dependências. Só insere o que falta."""
    resumo = carregar_base(sessao)
    resumo["marca"] = carregar_marcas(sessao)
    resumo.update(carregar_itens(sessao))
    resumo.update(carregar_seguranca(sessao))
    resumo["municipio"] = carregar_municipios(sessao)
    resumo["municipio_excecao"] = aplicar_excecoes(sessao)
    return resumo
```

`api/seed/__main__.py`:
```python
"""Carrega o conteúdo no banco: docker compose run --rm api python -m seed"""
from sqlalchemy.orm import Session

from app.db.sessao import obter_engine
from seed.carregar import carregar_tudo


def main() -> None:
    with Session(obter_engine()) as sessao, sessao.begin():
        resumo = carregar_tudo(sessao)
    for tabela, novas in resumo.items():
        print(f"{tabela}: {novas} novo(s)")


if __name__ == "__main__":
    main()
```

`api/seed/dados/seguranca.yaml` (texto próprio; bases a conferir nas fontes):
```yaml
- codigo: inmetro-cordoes
  tema: geral
  idade_inicio_meses: 0
  idade_fim_meses: 12
  texto: Prefira produtos infantis com selo INMETRO. Nada de cordão no pescoço nem prendedor de chupeta comprido.
  base: INMETRO
  itens: [berco, bebe-conforto, carrinho, cadeira-alimentacao, banheira]
- codigo: sono-seguro
  tema: sono
  idade_inicio_meses: 0
  idade_fim_meses: 12
  texto: O bebê dorme de barriga para cima, no próprio berço, em colchão firme, sem travesseiro, edredom, protetor de grade ou bichos de pelúcia.
  base: SBP
  itens: [berco, colchao-berco, lencol-elastico, saco-dormir, almofada-amamentacao, manta]
- codigo: transporte-bebe-conforto
  tema: transporte
  idade_inicio_meses: 0
  idade_fim_meses: 12
  texto: No carro, sempre no bebê conforto, voltado para trás e no banco traseiro, desde a saída da maternidade.
  base: CONTRAN
  itens: [bebe-conforto]
- codigo: banho-e-trocador
  tema: banho
  idade_inicio_meses: 0
  idade_fim_meses: 6
  texto: Nunca deixe o bebê sozinho no trocador ou na banheira, nem por um instante. A água do banho fica entre 36 e 37 °C.
  base: SBP
  itens: [banheira, comoda-trocador]
- codigo: sling-rosto-visivel
  tema: transporte
  idade_inicio_meses: 0
  idade_fim_meses: 6
  texto: No sling, o rosto do bebê fica sempre visível e o queixo longe do peito.
  base: Carregamento ergonômico
  itens: [sling]
- codigo: introducao-alimentar
  tema: alimentacao
  idade_inicio_meses: 6
  idade_fim_meses: 9
  texto: A introdução alimentar começa aos 6 meses, com o bebê sentado e de cinto. Sem mel até 1 ano e sem açúcar até 2 anos.
  base: SBP
  itens: [cadeira-alimentacao, kit-introducao, copo-transicao]
- codigo: casa-antes-de-engatinhar
  tema: casa
  idade_inicio_meses: 6
  idade_fim_meses: 12
  texto: Antes de o bebê engatinhar, proteja tomadas, gavetas e escadas e fixe os móveis na parede.
  base: SBP
  itens: [protetor-tomada, trava-gaveta, portao-seguranca, protetor-quina, comoda-trocador]
- codigo: andador-e-brinquedos
  tema: brinquedos
  idade_inicio_meses: 6
  idade_fim_meses: 12
  texto: Andador não é recomendado. Brinquedos para a faixa de 0 a 3 anos, sem peças pequenas.
  base: SBP, INMETRO
  itens: []
```

- [ ] **Step 4: Rodar e ver passar**

Run: `docker compose run --rm api pytest`
Expected: `37 passed`.

- [ ] **Step 5: Carregar o banco de desenvolvimento**

Run: `docker compose run --rm api python -m seed`
Expected: linhas como `item: 47 novo(s)`, `municipio: 5571 novo(s)`, `regra_seguranca: 8 novo(s)`. Rode de novo: todas as linhas com `0 novo(s)`.

Acrescente ao `README.md`, antes de `## Testes`:
````markdown
## Banco e conteúdo

```bash
docker compose run --rm api alembic upgrade head   # cria/atualiza as tabelas
docker compose run --rm api python -m seed         # carrega o conteúdo (só o que falta)
```

O conteúdo inicial fica em `api/seed/dados/`. Depois da primeira carga, edite pelo admin
(`/admin`): o seed nunca sobrescreve o que já está no banco.
````

- [ ] **Step 6: Commit**

```bash
git add api/seed api/tests/carga README.md
git commit -m "feat: regras de segurança e comando de carga do conteúdo

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: Admin do conteúdo (SQLAdmin) em `/admin`

**Files:**
- Create: `api/app/admin/__init__.py`
- Modify: `api/app/main.py`
- Test: `api/tests/test_admin.py`

**Interfaces:**
- Consumes: modelos do catálogo (Task 3), `Configuracoes` (Task 1).
- Produces: `app.admin.montar_admin(app: FastAPI, engine: Engine) -> None`; `app.main.criar_app(cfg: Configuracoes | None = None) -> FastAPI` (novo parâmetro opcional). As tabelas da família **não** aparecem no admin.

- [ ] **Step 1: Escrever os testes que falham**

`api/tests/test_admin.py`:
```python
from fastapi.testclient import TestClient

import os

from app.config import Configuracoes
from app.main import criar_app

URL_TESTE = os.environ["TEST_DATABASE_URL"]


def _cliente(admin: bool) -> TestClient:
    cfg = Configuracoes(database_url=URL_TESTE, admin_habilitado=admin)
    return TestClient(criar_app(cfg))


def test_admin_desligado_nao_existe(engine_teste):
    assert _cliente(admin=False).get("/admin/").status_code == 404


def test_admin_ligado_lista_itens(engine_teste):
    cliente = _cliente(admin=True)

    assert cliente.get("/admin/").status_code == 200
    resposta = cliente.get("/admin/item/list")
    assert resposta.status_code == 200
    assert "Itens" in resposta.text


def test_admin_nao_mostra_dados_das_familias(engine_teste):
    cliente = _cliente(admin=True)

    assert cliente.get("/admin/enxoval/list").status_code == 404
```

- [ ] **Step 2: Rodar e ver falhar**

Run: `docker compose run --rm api pytest tests/test_admin.py`
Expected: FAIL com `TypeError: criar_app() takes 0 positional arguments but 1 was given`

- [ ] **Step 3: Implementar**

`api/app/admin/__init__.py`:
```python
"""Admin do conteúdo. Só é montado com ADMIN_HABILITADO=true.

Antes de ir para produção, precisa estar protegido pelo Keycloak (bloqueio de deploy).
"""
from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqlalchemy import Engine

from app.db.catalogo import (
    Categoria,
    Estado,
    FaseRoteiro,
    Item,
    ItemMarca,
    ItemRegra,
    ItemTamanho,
    JanelaTamanho,
    Marca,
    Municipio,
    PerfilClima,
    RegraSeguranca,
)


class ItemAdmin(ModelView, model=Item):
    name, name_plural, icon = "Item", "Itens", "fa-solid fa-baby"
    column_list = [Item.nome, Item.categoria, Item.prioridade_base, Item.e_seguranca]
    column_searchable_list = [Item.nome, Item.slug]
    column_sortable_list = [Item.nome, Item.prioridade_base]


class ItemTamanhoAdmin(ModelView, model=ItemTamanho):
    name, name_plural, icon = "Quantidade por tamanho", "Quantidades por tamanho", "fa-solid fa-ruler"
    column_list = [ItemTamanho.item, ItemTamanho.tamanho, ItemTamanho.quantidade_base]


class ItemRegraAdmin(ModelView, model=ItemRegra):
    name, name_plural, icon = "Regra do item", "Regras dos itens", "fa-solid fa-code-branch"
    column_list = [ItemRegra.item, ItemRegra.condicao, ItemRegra.efeito, ItemRegra.valor]


class MarcaAdmin(ModelView, model=Marca):
    name, name_plural, icon = "Marca", "Marcas", "fa-solid fa-tag"
    column_list = [Marca.nome, Marca.faixa_padrao, Marca.validado, Marca.revisado_em]
    column_searchable_list = [Marca.nome]
    column_sortable_list = [Marca.nome, Marca.validado]


class ItemMarcaAdmin(ModelView, model=ItemMarca):
    name, name_plural, icon = "Marca do item", "Marcas dos itens", "fa-solid fa-link"
    column_list = [ItemMarca.item, ItemMarca.marca, ItemMarca.faixa, ItemMarca.ordem]


class RegraSegurancaAdmin(ModelView, model=RegraSeguranca):
    name, name_plural, icon = "Regra de segurança", "Regras de segurança", "fa-solid fa-shield-heart"
    column_list = [
        RegraSeguranca.codigo,
        RegraSeguranca.tema,
        RegraSeguranca.idade_inicio_meses,
        RegraSeguranca.idade_fim_meses,
        RegraSeguranca.validado,
    ]


class CategoriaAdmin(ModelView, model=Categoria):
    name, name_plural, icon = "Categoria", "Categorias", "fa-solid fa-layer-group"
    column_list = [Categoria.nome, Categoria.ordem]


class FaseRoteiroAdmin(ModelView, model=FaseRoteiro):
    name, name_plural, icon = "Fase do roteiro", "Fases do roteiro", "fa-solid fa-route"
    column_list = [FaseRoteiro.ordem, FaseRoteiro.nome, FaseRoteiro.inicio, FaseRoteiro.fim]


class JanelaTamanhoAdmin(ModelView, model=JanelaTamanho):
    name, name_plural, icon = "Janela de tamanho", "Janelas de tamanho", "fa-solid fa-calendar"
    column_list = [
        JanelaTamanho.tamanho,
        JanelaTamanho.idade_inicio_dias,
        JanelaTamanho.idade_fim_dias,
    ]


class PerfilClimaAdmin(ModelView, model=PerfilClima):
    name, name_plural, icon = "Perfil de clima", "Perfis de clima", "fa-solid fa-temperature-half"
    column_list = [PerfilClima.nome, PerfilClima.meses_frios, PerfilClima.meses_frescos]


class EstadoAdmin(ModelView, model=Estado):
    name, name_plural, icon = "Estado", "Estados", "fa-solid fa-map"
    column_list = [Estado.uf, Estado.nome, Estado.perfil_padrao]


class MunicipioAdmin(ModelView, model=Municipio):
    name, name_plural, icon = "Município", "Municípios", "fa-solid fa-city"
    column_list = [Municipio.nome, Municipio.uf, Municipio.perfil_excecao]
    column_searchable_list = [Municipio.nome, Municipio.nome_busca]
    form_excluded_columns = [Municipio.nome_busca]


VISOES = [
    ItemAdmin,
    ItemTamanhoAdmin,
    ItemRegraAdmin,
    MarcaAdmin,
    ItemMarcaAdmin,
    RegraSegurancaAdmin,
    CategoriaAdmin,
    FaseRoteiroAdmin,
    JanelaTamanhoAdmin,
    PerfilClimaAdmin,
    EstadoAdmin,
    MunicipioAdmin,
]


def montar_admin(app: FastAPI, engine: Engine) -> None:
    admin = Admin(app, engine, base_url="/admin", title="Enxoval Inteligente · Conteúdo")
    for visao in VISOES:
        admin.add_view(visao)
```

Substitua `api/app/main.py` por:
```python
from fastapi import APIRouter, FastAPI
from sqlalchemy import create_engine

from app.admin import montar_admin
from app.config import Configuracoes, obter_configuracoes
from app.rotas import saude


def criar_app(cfg: Configuracoes | None = None) -> FastAPI:
    cfg = cfg or obter_configuracoes()
    app = FastAPI(
        title="Enxoval Inteligente",
        docs_url="/api/docs" if cfg.docs_habilitado else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if cfg.docs_habilitado else None,
    )
    api = APIRouter(prefix="/api/v1")
    api.include_router(saude.router)
    app.include_router(api)
    if cfg.admin_habilitado:
        montar_admin(app, create_engine(cfg.database_url, pool_pre_ping=True))
    return app


app = criar_app()
```

Atenção: o município não tem campo para editar `nome_busca` no formulário. Se você **renomear** um município no admin, a busca continua usando o nome antigo até a Etapa 3, que vai recalcular `nome_busca` ao salvar (registrado para a Etapa 3).

- [ ] **Step 4: Rodar e ver passar**

Run: `docker compose run --rm api pytest`
Expected: `40 passed`

- [ ] **Step 5: Conferir no navegador**

Run: `docker compose up -d` e abra http://localhost:8000/admin
Expected: menu com Itens, Marcas, Regras de segurança, Municípios etc. Abra "Itens", procure "berço", edite o nome, salve e confira que mudou. Volte o nome ao original.

- [ ] **Step 6: Commit**

```bash
git add api
git commit -m "feat: admin do conteúdo com SQLAdmin, ligado só por variável de ambiente

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

## Ao terminar a Etapa 1

- `docker compose run --rm api pytest` → 40 testes passando.
- Banco de desenvolvimento migrado e carregado (`python -m seed` repetido mostra só zeros).
- `/admin` editando o conteúdo; `/api/v1/saude` respondendo `{"status":"ok","banco":"ok"}`.
- Próximo passo: escrever o plano da **Etapa 2 (motor de personalização)** sobre este código.
