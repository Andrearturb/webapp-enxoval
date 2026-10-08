"""Dependências do FastAPI que os testes sobrescrevem.

Centraliza as factories de dependência injetável usadas nas rotas.
Manter aqui — e não espalhadas nas rotas — facilita o override em testes.
"""
from datetime import date

from fastapi import Depends
from sqlalchemy.orm import Session

from app.acesso import DonoId
from app.db.sessao import obter_sessao
from app.servicos.enxoval_service import EnxovalService


def obter_hoje() -> date:
    """Retorna a data de hoje — único ponto do projeto que lê o relógio.

    O motor recebe a data como parâmetro para não depender do relógio diretamente,
    o que facilita testes sem mocks de ``datetime``.
    """
    return date.today()


def obter_servico(
    dono_id: DonoId,
    sessao: Session = Depends(obter_sessao),
    hoje: date = Depends(obter_hoje),
) -> EnxovalService:
    """Cria e injeta um ``EnxovalService`` configurado para o request atual.

    Injeta o ``dono_id`` extraído do token JWT para que o serviço filtre
    e proteja os enxovais por proprietário.

    Args:
        dono_id: ``sub`` do JWT Keycloak (ou ``None`` em modo dev sem auth).
        sessao: Sessão SQLAlchemy fornecida pelo ``obter_sessao``.
        hoje: Data de hoje fornecida pelo ``obter_hoje``.

    Returns:
        Instância de ``EnxovalService`` pronta para uso no handler.
    """
    return EnxovalService(sessao, hoje, dono_id=dono_id)
