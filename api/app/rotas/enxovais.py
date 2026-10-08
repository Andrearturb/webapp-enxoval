"""Rotas do ciclo de vida do enxoval: listar, criar, ler, editar e apagar.

Todas as operações delegam para ``EnxovalService``, que encapsula a lógica
de negócio, o controle de acesso por dono e o acesso ao banco.
"""
import uuid

from fastapi import APIRouter, Depends, Request, Response, status
from sqlalchemy.orm import Session

from app.acesso import verificar_acesso
from app.config import obter_configuracoes
from app.db.catalogo import Municipio
from app.db.sessao import obter_sessao
from app.dependencias import obter_servico
from app.limite import LimitePorIp
from app.rotas.schemas import (
    EnxovalCriado,
    EnxovalResumo,
    EnxovalSaida,
    Erro,
    RespostasEntrada,
)
from app.servicos.apresentacao import montar_resumo, montar_saida
from app.servicos.enxoval_service import EnxovalService

MAXIMO_CRIACOES = obter_configuracoes().limite_criacao_maximo
JANELA_SEGUNDOS = 3600
limite_de_criacao = LimitePorIp(MAXIMO_CRIACOES, JANELA_SEGUNDOS)

router = APIRouter(
    prefix="/enxovais",
    tags=["enxoval"],
    responses={404: {"model": Erro}, 422: {"model": Erro}},
    dependencies=[Depends(verificar_acesso)],
)


@router.get("", response_model=list[EnxovalResumo])
def listar(
    sessao: Session = Depends(obter_sessao),
    servico: EnxovalService = Depends(obter_servico),
) -> list[EnxovalResumo]:
    """Lista os enxovais do dono com o mesmo progresso exibido na planilha."""
    enxovais = servico.listar()
    resumos = []
    for enxoval in enxovais:
        municipio = sessao.get(Municipio, enxoval.municipio_codigo)
        percentual = servico.ler(enxoval.id).progresso.percentual
        resumos.append(montar_resumo(enxoval, municipio, percentual))
    return resumos


@router.post("", response_model=EnxovalCriado, status_code=status.HTTP_201_CREATED)
def criar(
    entrada: RespostasEntrada,
    resposta: Response,
    pedido: Request,
    sessao: Session = Depends(obter_sessao),
    servico: EnxovalService = Depends(obter_servico),
) -> EnxovalCriado:
    """Cria um enxoval a partir das respostas do questionário.

    Aplica rate limiting por IP (20 criações/hora) para evitar abuso.
    Retorna o UUID gerado no cabeçalho ``Location`` além do corpo.
    """
    limite_de_criacao.verificar(pedido.client.host if pedido.client else "desconhecido")
    dados = entrada.para_servico()
    enxoval = servico.criar(
        municipio_codigo=dados.municipio_codigo,
        data_prevista=dados.data_prevista,
        dias_entre_lavagens=dados.dias_entre_lavagens,
        moradia=dados.moradia,
        tem_carro=dados.tem_carro,
        orcamento=dados.orcamento,
        primeiro_filho=dados.primeiro_filho,
        correcao_perfil=dados.correcao_perfil,
    )
    sessao.commit()
    resposta.headers["Location"] = f"/api/v1/enxovais/{enxoval.id}"
    return EnxovalCriado(id=enxoval.id)


@router.get("/{enxoval_id}", response_model=EnxovalSaida)
def ler(
    enxoval_id: uuid.UUID,
    servico: EnxovalService = Depends(obter_servico),
) -> EnxovalSaida:
    """Retorna o enxoval completo: linhas calculadas, roteiro, fichas e progresso."""
    return montar_saida(servico.ler(enxoval_id))


@router.patch("/{enxoval_id}", response_model=EnxovalSaida)
def editar(
    enxoval_id: uuid.UUID,
    entrada: RespostasEntrada,
    sessao: Session = Depends(obter_sessao),
    servico: EnxovalService = Depends(obter_servico),
) -> EnxovalSaida:
    """Substitui todas as respostas do questionário. Marcações são preservadas."""
    dados = entrada.para_servico()
    servico.editar(
        enxoval_id=enxoval_id,
        municipio_codigo=dados.municipio_codigo,
        data_prevista=dados.data_prevista,
        dias_entre_lavagens=dados.dias_entre_lavagens,
        moradia=dados.moradia,
        tem_carro=dados.tem_carro,
        orcamento=dados.orcamento,
        primeiro_filho=dados.primeiro_filho,
        correcao_perfil=dados.correcao_perfil,
    )
    sessao.commit()
    return montar_saida(servico.ler(enxoval_id))


@router.post("/{enxoval_id}/prever", response_model=EnxovalSaida)
def prever(
    enxoval_id: uuid.UUID,
    entrada: RespostasEntrada,
    sessao: Session = Depends(obter_sessao),
    servico: EnxovalService = Depends(obter_servico),
) -> EnxovalSaida:
    """Calcula uma prévia sem persistir respostas nem alterar marcações."""
    dados = entrada.para_servico()
    with sessao.begin_nested() as transacao:
        servico.editar(
            enxoval_id=enxoval_id,
            municipio_codigo=dados.municipio_codigo,
            data_prevista=dados.data_prevista,
            dias_entre_lavagens=dados.dias_entre_lavagens,
            moradia=dados.moradia,
            tem_carro=dados.tem_carro,
            orcamento=dados.orcamento,
            primeiro_filho=dados.primeiro_filho,
            correcao_perfil=dados.correcao_perfil,
        )
        previa = montar_saida(servico.ler(enxoval_id))
        transacao.rollback()
    return previa


@router.delete("/{enxoval_id}", status_code=status.HTTP_204_NO_CONTENT)
def apagar(
    enxoval_id: uuid.UUID,
    sessao: Session = Depends(obter_sessao),
    servico: EnxovalService = Depends(obter_servico),
) -> Response:
    """Remove permanentemente o enxoval e todas as suas linhas."""
    servico.apagar(enxoval_id)
    sessao.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
