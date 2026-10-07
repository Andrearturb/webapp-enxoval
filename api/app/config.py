from functools import lru_cache

from pydantic_settings import BaseSettings


class Configuracoes(BaseSettings):
    """Lidas das variáveis de ambiente (DATABASE_URL, ADMIN_HABILITADO...).

    Attributes:
        database_url: URL de conexão com o PostgreSQL.
        admin_habilitado: Liga o painel ``/admin`` (desligado por padrão em produção).
        docs_habilitado: Liga o OpenAPI em ``/api/docs`` (desligado por padrão em produção).
        limite_criacao_maximo: Máximo de criações de enxoval por IP/hora.
            Pode ser aumentado via variável de ambiente ``LIMITE_CRIACAO_MAXIMO``
            para facilitar testes E2E sem 429.
    """

    database_url: str
    admin_habilitado: bool = False
    docs_habilitado: bool = False
    limite_criacao_maximo: int = 20


@lru_cache
def obter_configuracoes() -> Configuracoes:
    return Configuracoes()
