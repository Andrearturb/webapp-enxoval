import os

from fastapi.testclient import TestClient

from app.config import Configuracoes
from app.main import criar_app

URL_TESTE = os.environ["TEST_DATABASE_URL"]


def _cliente(admin: bool) -> TestClient:
    cfg = Configuracoes(database_url=URL_TESTE, admin_habilitado=admin)
    return TestClient(criar_app(cfg))


def test_admin_desligado_nao_existe(engine_teste):
    assert _cliente(admin=False).get("/admin/").status_code == 404


def test_admin_ligado_lista_itens(engine_teste):
    cliente = _cliente(admin=True)

    assert cliente.get("/admin/").status_code == 200
    resposta = cliente.get("/admin/item/list")
    assert resposta.status_code == 200
    assert "Itens" in resposta.text


def test_admin_nao_mostra_dados_das_familias(engine_teste):
    cliente = _cliente(admin=True)

    assert cliente.get("/admin/enxoval/list").status_code == 404
