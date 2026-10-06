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
