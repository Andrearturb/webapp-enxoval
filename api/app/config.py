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
