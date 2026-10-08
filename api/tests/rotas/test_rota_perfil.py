import base64
import io

import pytest
from PIL import Image


def _foto(formato="PNG"):
    buffer = io.BytesIO()
    Image.new("RGB", (800, 600), "green").save(buffer, format=formato)
    return buffer.getvalue()


def test_perfil_foto_salva_normaliza_e_remove(cliente):
    assert cliente.get("/api/v1/perfil").json() == {"foto": None}
    resposta = cliente.put("/api/v1/perfil/foto", content=_foto(), headers={"Content-Type": "image/png"})
    assert resposta.status_code == 200
    assert resposta.headers["cache-control"] == "no-store"
    foto = resposta.json()["foto"]
    with Image.open(io.BytesIO(base64.b64decode(foto.split(",")[1]))) as imagem:
        assert imagem.format == "JPEG"
        assert max(imagem.size) <= 512
        assert not imagem.getexif()
    assert cliente.get("/api/v1/perfil").json()["foto"] == foto
    assert cliente.delete("/api/v1/perfil/foto").status_code == 204
    assert cliente.get("/api/v1/perfil").json()["foto"] is None


def test_foto_privada_por_usuario(cliente):
    from app.acesso import verificar_acesso
    original = cliente.app.dependency_overrides[verificar_acesso]
    cliente.put("/api/v1/perfil/foto", content=_foto())
    cliente.app.dependency_overrides[verificar_acesso] = lambda: "outra-conta"
    assert cliente.get("/api/v1/perfil").json()["foto"] is None
    cliente.delete("/api/v1/perfil/foto")
    cliente.app.dependency_overrides[verificar_acesso] = original
    assert cliente.get("/api/v1/perfil").json()["foto"] is not None


@pytest.mark.parametrize("dados,status", [(b"<svg></svg>", 422), (b"nao-e-foto", 422), (b"x" * (2*1024*1024+1), 413), (_foto("GIF"), 422)])
def test_foto_rejeita_arquivo_invalido_sem_apagar_anterior(cliente, dados, status):
    foto = cliente.put("/api/v1/perfil/foto", content=_foto()).json()["foto"]
    assert cliente.put("/api/v1/perfil/foto", content=dados).status_code == status
    assert cliente.get("/api/v1/perfil").json()["foto"] == foto


def test_perfil_exige_usuario_mesmo_em_modo_dev(cliente):
    from app.acesso import verificar_acesso
    cliente.app.dependency_overrides[verificar_acesso] = lambda: None
    assert cliente.get("/api/v1/perfil").status_code == 401
    assert cliente.put("/api/v1/perfil/foto", content=_foto()).status_code == 401
    assert cliente.delete("/api/v1/perfil/foto").status_code == 401
