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
