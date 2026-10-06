import uuid
from datetime import date

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.acesso import verificar_acesso
from app.db.sessao import obter_sessao
from app.dependencias import obter_hoje
from app.limite import LimitePorIp
from app.rotas.schemas import (
    EnxovalCriado,
    EnxovalSaida,
    Erro,
    RespostasEntrada,
    montar_saida,
)
from app.servicos.escrita import apagar_enxoval, criar_enxoval, editar_respostas
from app.servicos.leitura import ler_enxoval

MAXIMO_CRIACOES = 20
JANELA_SEGUNDOS = 3600
limite_de_criacao = LimitePorIp(MAXIMO_CRIACOES, JANELA_SEGUNDOS)

router = APIRouter(
    prefix="/enxovais",
    tags=["enxoval"],
    responses={404: {"model": Erro}, 422: {"model": Erro}},
    dependencies=[Depends(verificar_acesso)],
)


@router.post("", response_model=EnxovalCriado, status_code=status.HTTP_201_CREATED)
def criar(
    entrada: RespostasEntrada,
    resposta: Response,
    pedido: Request,
    sessao: Session = Depends(obter_sessao),
    hoje: date = Depends(obter_hoje),
) -> EnxovalCriado:
    limite_de_criacao.verificar(pedido.client.host if pedido.client else "desconhecido")
    enxoval = criar_enxoval(sessao, entrada.para_servico(), hoje)
    sessao.commit()
    resposta.headers["Location"] = f"/api/v1/enxovais/{enxoval.id}"
    return EnxovalCriado(id=enxoval.id)


@router.get("/{enxoval_id}", response_model=EnxovalSaida)
def ler(
    enxoval_id: uuid.UUID,
    sessao: Session = Depends(obter_sessao),
    hoje: date = Depends(obter_hoje),
) -> EnxovalSaida:
    return montar_saida(ler_enxoval(sessao, enxoval_id, hoje))


@router.patch("/{enxoval_id}", response_model=EnxovalSaida)
def editar(
    enxoval_id: uuid.UUID,
    entrada: RespostasEntrada,
    sessao: Session = Depends(obter_sessao),
    hoje: date = Depends(obter_hoje),
) -> EnxovalSaida:
    """Recebe as 6 respostas inteiras; não há edição parcial no MVP."""
    editar_respostas(sessao, enxoval_id, entrada.para_servico(), hoje)
    sessao.commit()
    return montar_saida(ler_enxoval(sessao, enxoval_id, hoje))


@router.delete("/{enxoval_id}", status_code=status.HTTP_204_NO_CONTENT)
def apagar(
    enxoval_id: uuid.UUID, sessao: Session = Depends(obter_sessao)
) -> Response:
    apagar_enxoval(sessao, enxoval_id)
    sessao.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
