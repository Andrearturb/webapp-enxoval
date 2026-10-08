import pytest

from app.acesso import verificar_acesso
from app.db.perfil import PerfilUsuario
from tests.conftest import DONO_FIXO


@pytest.mark.parametrize("avatar", ["ursinho", "coelhinho", "elefantinho", "patinho", "nuvem", "lua"])
def test_avatar_salva_e_persiste(cliente, avatar):
    assert cliente.get("/api/v1/perfil").json() == {"avatar": "ursinho"}
    resposta = cliente.put("/api/v1/perfil/avatar", json={"avatar": avatar})
    assert resposta.status_code == 200
    assert resposta.headers["cache-control"] == "no-store"
    assert resposta.json() == {"avatar": avatar}
    assert cliente.get("/api/v1/perfil").json() == resposta.json()
    assert cliente.delete("/api/v1/perfil/avatar").status_code == 405
    assert cliente.get("/api/v1/perfil").json() == {"avatar": avatar}


def test_avatar_isolado_por_usuario(cliente):
    original = cliente.app.dependency_overrides[verificar_acesso]
    cliente.put("/api/v1/perfil/avatar", json={"avatar": "ursinho"})
    cliente.app.dependency_overrides[verificar_acesso] = lambda: "outra-conta"
    assert cliente.get("/api/v1/perfil").json() == {"avatar": "ursinho"}
    cliente.put("/api/v1/perfil/avatar", json={"avatar": "lua"})
    assert cliente.get("/api/v1/perfil").json()["avatar"] == "lua"
    cliente.app.dependency_overrides[verificar_acesso] = original
    assert cliente.get("/api/v1/perfil").json()["avatar"] == "ursinho"


@pytest.mark.parametrize("avatar", ["desconhecido", "../../foto", "https://example.com/imagem.png", "Ursinho", None])
def test_avatar_invalido_nao_apaga_escolha(cliente, avatar):
    anterior = cliente.put("/api/v1/perfil/avatar", json={"avatar": "nuvem"}).json()
    assert cliente.put("/api/v1/perfil/avatar", json={"avatar": avatar}).status_code == 422
    assert cliente.get("/api/v1/perfil").json() == anterior


def test_perfil_nunca_expoe_foto_antiga(cliente, sessao):
    dados = b"foto-antiga-preservada"
    sessao.add(PerfilUsuario(dono_id=DONO_FIXO, foto=dados))
    sessao.commit()
    assert cliente.get("/api/v1/perfil").json() == {"avatar": "ursinho"}
    assert cliente.put("/api/v1/perfil/avatar", json={"avatar": "invalido"}).status_code == 422
    assert sessao.get(PerfilUsuario, DONO_FIXO).foto == dados
    assert cliente.put("/api/v1/perfil/avatar", json={"avatar": "coelhinho"}).json() == {"avatar": "coelhinho"}
    assert sessao.get(PerfilUsuario, DONO_FIXO).foto is None


def test_upload_de_foto_foi_retirado(cliente):
    assert cliente.put("/api/v1/perfil/foto", content=b"imagem").status_code == 404


def test_perfil_exige_usuario_mesmo_em_modo_dev(cliente):
    cliente.app.dependency_overrides[verificar_acesso] = lambda: None
    assert cliente.get("/api/v1/perfil").status_code == 401
    assert cliente.put("/api/v1/perfil/avatar", json={"avatar": "ursinho"}).status_code == 401
