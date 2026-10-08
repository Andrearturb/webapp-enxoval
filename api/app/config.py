"""Configurações da aplicação lidas via variáveis de ambiente.

Todas as variáveis têm valores padrão seguros para desenvolvimento local.
Em produção, sobrescreva via variáveis de ambiente ou arquivo .env.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings


class Configuracoes(BaseSettings):
    """Configurações lidas das variáveis de ambiente.

    Attributes:
        database_url: URL de conexão PostgreSQL para a aplicação.
        admin_habilitado: Liga o painel ``/admin`` (desligar em produção).
        docs_habilitado: Liga o OpenAPI em ``/api/docs`` (desligar em produção).
        limite_criacao_maximo: Máximo de criações de enxoval por IP/hora.
        keycloak_url: URL base do Keycloak (ex.: ``http://keycloak:8080``).
        keycloak_realm: Nome do realm configurado no Keycloak.
        keycloak_client_id: Client ID do app registrado no realm.
        keycloak_habilitado: Ativa a validação de JWT em todas as rotas.
            ``False`` em dev sem Keycloak no ar — todas as requisições passam.
            ``True`` em produção — token obrigatório em todas as rotas de enxoval.
    """

    database_url: str
    admin_habilitado: bool = False
    docs_habilitado: bool = False
    limite_criacao_maximo: int = 20

    # Keycloak
    keycloak_url: str = "http://localhost:8080"
    keycloak_issuer: str | None = None
    keycloak_realm: str = "enxoval"
    keycloak_client_id: str = "webapp"
    keycloak_habilitado: bool = False


@lru_cache
def obter_configuracoes() -> Configuracoes:
    """Retorna as configurações em cache (lidas uma única vez por processo)."""
    return Configuracoes()
