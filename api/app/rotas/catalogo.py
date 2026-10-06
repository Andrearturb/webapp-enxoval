from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import case, or_, select
from sqlalchemy.orm import Session

from app.db import catalogo as tabelas
from app.db.enums import PerfilCodigo
from app.db.sessao import obter_sessao
from app.rotas.schemas import PerfilSaida
from app.texto import normalizar_busca

MINIMO_BUSCA = 2
LIMITE_BUSCA = 10

router = APIRouter(tags=["catálogo"])


class MunicipioBuscaSaida(BaseModel):
    codigo_ibge: int
    nome: str
    uf: str
    perfil_sugerido: PerfilCodigo


@router.get("/perfis-clima", response_model=list[PerfilSaida])
def listar_perfis(sessao: Session = Depends(obter_sessao)) -> list[PerfilSaida]:
    perfis = sessao.scalars(select(tabelas.PerfilClima).order_by(tabelas.PerfilClima.id)).all()
    return [
        PerfilSaida(
            codigo=p.codigo, nome=p.nome, descricao=p.descricao,
            meses_frios=list(p.meses_frios or ()), meses_frescos=list(p.meses_frescos or ()),
        )
        for p in perfis
    ]


@router.get("/municipios", response_model=list[MunicipioBuscaSaida])
def buscar_municipios(
    busca: str = Query(max_length=80),
    sessao: Session = Depends(obter_sessao),
) -> list[MunicipioBuscaSaida]:
    """Autocompletar de cidade. Casa por prefixo do nome ou de qualquer palavra dele."""
    alvo = normalizar_busca(busca)
    if len(alvo) < MINIMO_BUSCA:
        return []
    municipios = sessao.scalars(
        select(tabelas.Municipio)
        .join(tabelas.Estado)
        .where(
            or_(
                tabelas.Municipio.nome_busca.like(f"{alvo}%"),
                tabelas.Municipio.nome_busca.like(f"% {alvo}%"),
            )
        )
        .order_by(
            # Correspondência exata e por prefixo vêm antes de "contém a palavra",
            # senão um município muito buscado some atrás de 10 que só citam a
            # palavra depois do nome (ex.: "Serra" atrás de "Amparo do Serra").
            case(
                (tabelas.Municipio.nome_busca == alvo, 0),
                (tabelas.Municipio.nome_busca.like(f"{alvo}%"), 1),
                else_=2,
            ),
            tabelas.Municipio.nome,
            tabelas.Municipio.uf,
        )
        .limit(LIMITE_BUSCA)
        .options()
    ).all()
    return [
        MunicipioBuscaSaida(
            codigo_ibge=m.codigo_ibge,
            nome=m.nome,
            uf=m.uf,
            perfil_sugerido=m.perfil_excecao or m.estado.perfil_padrao,
        )
        for m in municipios
    ]
