import base64
import io
import warnings

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from PIL import Image, ImageOps, UnidentifiedImageError
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.acesso import DonoId
from app.db.perfil import PerfilUsuario
from app.db.sessao import obter_sessao

router = APIRouter(prefix="/perfil", tags=["perfil"])
MAXIMO_BYTES = 2 * 1024 * 1024
MAXIMO_PIXELS = 16_000_000


class PerfilSaida(BaseModel):
    foto: str | None = None


def _dono(dono_id: str | None) -> str:
    if not dono_id:
        raise HTTPException(401, detail={"erro": "autenticacao_necessaria", "mensagem": "Entre na sua conta para editar seu perfil."})
    return dono_id


def _saida(perfil: PerfilUsuario | None) -> PerfilSaida:
    return PerfilSaida(foto="data:image/jpeg;base64," + base64.b64encode(perfil.foto).decode() if perfil else None)


@router.get("", response_model=PerfilSaida)
def ler(dono_id: DonoId, sessao: Session = Depends(obter_sessao)) -> PerfilSaida:
    return _saida(sessao.get(PerfilUsuario, _dono(dono_id)))


@router.put("/foto", response_model=PerfilSaida)
async def salvar_foto(request: Request, dono_id: DonoId, sessao: Session = Depends(obter_sessao)) -> PerfilSaida:
    dono = _dono(dono_id)
    dados = bytearray()
    async for parte in request.stream():
        dados.extend(parte)
        if len(dados) > MAXIMO_BYTES:
            raise HTTPException(413, detail={"erro": "foto_grande", "mensagem": "Escolha uma foto de até 2 MB."})
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(dados)) as original:
                if original.format not in ("JPEG", "PNG", "WEBP") or original.width * original.height > MAXIMO_PIXELS:
                    raise ValueError("Formato ou dimensões inválidos")
                original.load()
                foto = ImageOps.exif_transpose(original)
                foto.thumbnail((512, 512))
                # Reencodar remove metadados e conteúdo extra do arquivo original.
                rgba = foto.convert("RGBA")
                fundo = Image.new("RGB", rgba.size, "white")
                fundo.paste(rgba, mask=rgba.getchannel("A"))
                buffer = io.BytesIO()
                fundo.save(buffer, format="JPEG", quality=85, optimize=True)
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning):
        raise HTTPException(422, detail={"erro": "foto_invalida", "mensagem": "Escolha uma imagem JPG, PNG ou WebP válida, com até 16 megapixels."})
    perfil = sessao.get(PerfilUsuario, dono)
    if perfil is None:
        perfil = PerfilUsuario(dono_id=dono, foto=buffer.getvalue())
        sessao.add(perfil)
    else:
        perfil.foto = buffer.getvalue()
    sessao.commit()
    return _saida(perfil)


@router.delete("/foto", status_code=204)
def remover_foto(dono_id: DonoId, sessao: Session = Depends(obter_sessao)) -> Response:
    perfil = sessao.get(PerfilUsuario, _dono(dono_id))
    if perfil:
        sessao.delete(perfil)
        sessao.commit()
    return Response(status_code=204)
