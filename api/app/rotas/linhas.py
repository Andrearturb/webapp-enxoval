import uuid
from datetime import date

from fastapi import APIRouter, Depends, Path
from sqlalchemy.orm import Session

from app.acesso import verificar_acesso
from app.db.sessao import obter_sessao
from app.dependencias import obter_hoje
from app.rotas.schemas import (
    CompletarEntrada,
    EnxovalSaida,
    Erro,
    MarcacaoEntrada,
    montar_saida,
)
from app.servicos.escrita import completar_linha, marcar_linha
from app.servicos.leitura import ler_enxoval

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
    hoje: date = Depends(obter_hoje),
) -> EnxovalSaida:
    """Grava as quantidades da linha e devolve a lista e o progresso já atualizados."""
    marcar_linha(
        sessao, enxoval_id, chave, entrada.comprada, entrada.ganhada, entrada.ja_tinha
    )
    sessao.commit()
    return montar_saida(ler_enxoval(sessao, enxoval_id, hoje))


@router.post("/{chave}/completar", response_model=EnxovalSaida)
def completar(
    enxoval_id: uuid.UUID,
    entrada: CompletarEntrada,
    chave: str = CHAVE,
    sessao: Session = Depends(obter_sessao),
    hoje: date = Depends(obter_hoje),
) -> EnxovalSaida:
    completar_linha(sessao, enxoval_id, chave, entrada.origem, hoje)
    sessao.commit()
    return montar_saida(ler_enxoval(sessao, enxoval_id, hoje))
