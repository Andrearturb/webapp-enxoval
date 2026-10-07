"""Rotas de marcação de linhas da planilha.

Delega para ``EnxovalService`` e devolve o enxoval completo recalculado
após cada operação — o cliente sempre recebe o estado mais recente.
"""
import uuid

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.acesso import verificar_acesso
from app.db.sessao import obter_sessao
from app.dependencias import obter_servico
from app.rotas.schemas import (
    CompletarEntrada,
    EnxovalSaida,
    Erro,
    MarcacaoEntrada,
)
from app.servicos.apresentacao import montar_saida
from app.servicos.enxoval_service import EnxovalService

router = APIRouter(
    prefix="/enxovais/{enxoval_id}/linhas",
    tags=["enxoval"],
    responses={404: {"model": Erro}, 422: {"model": Erro}},
    dependencies=[Depends(verificar_acesso)],
)

CHAVE = Path(max_length=140, description="<slug>:<tamanho>:<variante>, ex.: body:P:frio")


@router.put("/{chave}", response_model=EnxovalSaida)
def marcar(
    enxoval_id: uuid.UUID,
    entrada: MarcacaoEntrada,
    chave: str = CHAVE,
    sessao: Session = Depends(obter_sessao),
    servico: EnxovalService = Depends(obter_servico),
) -> EnxovalSaida:
    """Grava as quantidades da linha e devolve a lista e o progresso atualizados."""
    servico.marcar_linha(enxoval_id, chave, entrada.comprada, entrada.ganhada, entrada.ja_tinha)
    sessao.commit()
    return montar_saida(servico.ler(enxoval_id))


@router.post("/{chave}/completar", response_model=EnxovalSaida)
def completar(
    enxoval_id: uuid.UUID,
    entrada: CompletarEntrada,
    chave: str = CHAVE,
    sessao: Session = Depends(obter_sessao),
    servico: EnxovalService = Depends(obter_servico),
) -> EnxovalSaida:
    """Completa o que falta na linha com a origem informada e devolve o estado atualizado."""
    servico.completar_linha(enxoval_id, chave, entrada.origem)
    sessao.commit()
    return montar_saida(servico.ler(enxoval_id))
