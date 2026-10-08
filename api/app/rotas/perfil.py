from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.acesso import DonoId
from app.db.perfil import PerfilUsuario
from app.db.sessao import obter_sessao

router = APIRouter(prefix="/perfil", tags=["perfil"])
AvatarCodigo = Literal["ursinho", "coelhinho", "elefantinho", "patinho", "nuvem", "lua"]


class PerfilSaida(BaseModel):
    avatar: AvatarCodigo = "ursinho"


class AvatarEntrada(BaseModel):
    avatar: AvatarCodigo


def _dono(dono_id: str | None) -> str:
    if not dono_id:
        raise HTTPException(401, detail={"erro": "autenticacao_necessaria", "mensagem": "Entre na sua conta para editar seu perfil."})
    return dono_id


def _saida(perfil: PerfilUsuario | None) -> PerfilSaida:
    return PerfilSaida(avatar=perfil.avatar if perfil and perfil.avatar else "ursinho")


@router.get("", response_model=PerfilSaida)
def ler(dono_id: DonoId, sessao: Session = Depends(obter_sessao)) -> PerfilSaida:
    return _saida(sessao.get(PerfilUsuario, _dono(dono_id)))


@router.put("/avatar", response_model=PerfilSaida)
def salvar_avatar(entrada: AvatarEntrada, dono_id: DonoId, sessao: Session = Depends(obter_sessao)) -> PerfilSaida:
    dono = _dono(dono_id)
    perfil = sessao.get(PerfilUsuario, dono)
    if perfil is None:
        perfil = PerfilUsuario(dono_id=dono, avatar=entrada.avatar)
        sessao.add(perfil)
    else:
        perfil.avatar = entrada.avatar
        perfil.foto = None
    sessao.commit()
    return _saida(perfil)
