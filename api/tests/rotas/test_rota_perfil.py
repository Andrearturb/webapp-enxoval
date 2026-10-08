import base64

import pytest

from app.acesso import verificar_acesso
from app.db.perfil import PerfilUsuario
from tests.conftest import DONO_FIXO


@pytest.mark.parametrize("avatar", ["ursinho", "coelhinho", "elefantinho", "patinho", "nuvem", "lua"])
def test_avatar_salva_persiste_e_volta_a_iniciais(cliente, avatar):
    assert cliente.get("/api/v1/perfil").json() == {"foto": None, "avatar": None}
    resposta = cliente.put("/api/v1/perfil/avatar", json={"avatar": avatar})
    assert resposta.status_code == 200
    assert resposta.headers["cache-control"] == "no-store"
    assert resposta.json() == {"foto": None, "avatar": avatar}
    assert cliente.get("/api/v1/perfil").json() == resposta.json()
    assert cliente.delete("/api/v1/perfil/avatar").status_code == 204
    assert cliente.get("/api/v1/perfil").json() == {"foto": None, "avatar": None}


def test_avatar_isolado_por_usuario(cliente):
    original = cliente.app.dependency_overrides[verificar_acesso]
    cliente.put("/api/v1/perfil/avatar", json={"avatar": "ursinho"})
    cliente.app.dependency_overrides[verificar_acesso] = lambda: "outra-conta"
    assert cliente.get("/api/v1/perfil").json() == {"foto": None, "avatar": None}
    cliente.put("/api/v1/perfil/avatar", json={"avatar": "lua"})
    cliente.delete("/api/v1/perfil/avatar")
    cliente.app.dependency_overrides[verificar_acesso] = original
    assert cliente.get("/api/v1/perfil").json()["avatar"] == "ursinho"


@pytest.mark.parametrize("avatar", ["desconhecido", "../../foto", "https://example.com/imagem.png", "Ursinho", None])
def test_avatar_invalido_nao_apaga_escolha(cliente, avatar):
    anterior = cliente.put("/api/v1/perfil/avatar", json={"avatar": "nuvem"}).json()
    assert cliente.put("/api/v1/perfil/avatar", json={"avatar": avatar}).status_code == 422
    assert cliente.get("/api/v1/perfil").json() == anterior


def test_foto_antiga_preservada_ate_usuario_escolher_avatar(cliente, sessao):
    dados = b"foto-antiga-preservada"
    sessao.add(PerfilUsuario(dono_id=DONO_FIXO, foto=dados))
    sessao.commit()
    foto = "data:image/jpeg;base64," + base64.b64encode(dados).decode()
    assert cliente.get("/api/v1/perfil").json() == {"foto": foto, "avatar": None}
    assert cliente.put("/api/v1/perfil/avatar", json={"avatar": "invalido"}).status_code == 422
    assert sessao.get(PerfilUsuario, DONO_FIXO).foto == dados
    assert cliente.put("/api/v1/perfil/avatar", json={"avatar": "coelhinho"}).json() == {"foto": None, "avatar": "coelhinho"}
    assert sessao.get(PerfilUsuario, DONO_FIXO).foto is None


def test_upload_de_foto_foi_retirado(cliente):
    assert cliente.put("/api/v1/perfil/foto", content=b"imagem").status_code == 404


def test_perfil_exige_usuario_mesmo_em_modo_dev(cliente):
    cliente.app.dependency_overrides[verificar_acesso] = lambda: None
    assert cliente.get("/api/v1/perfil").status_code == 401
    assert cliente.put("/api/v1/perfil/avatar", json={"avatar": "ursinho"}).status_code == 401
    assert cliente.delete("/api/v1/perfil/avatar").status_code == 401