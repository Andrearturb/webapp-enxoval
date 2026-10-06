from datetime import date

import pytest
from fastapi import APIRouter

from app.dependencias import obter_hoje
from app.erros import DadoInvalido, EnxovalNaoEncontrado
from app.main import criar_app


@pytest.fixture
def cliente_de_erros():
    from fastapi.testclient import TestClient

    from app.config import Configuracoes

    app = criar_app(Configuracoes(database_url="postgresql+psycopg://x/y"))
    testes = APIRouter(prefix="/api/v1/_teste")

    @testes.get("/nao-encontrado")
    def _nao_encontrado():
        raise EnxovalNaoEncontrado()

    @testes.get("/invalido")
    def _invalido():
        raise DadoInvalido("codigo_qualquer", "Mensagem em português.")

    @testes.get("/explode")
    def _explode():
        raise RuntimeError("detalhe interno que não pode aparecer")

    @testes.get("/explode/{enxoval_id}")
    def _explode_com_id(enxoval_id: str):
        raise RuntimeError(f"falhou para o enxoval {enxoval_id}")

    app.include_router(testes)
    return TestClient(app, raise_server_exceptions=False)


def test_erro_de_dominio_vira_404_no_formato_padrao(cliente_de_erros):
    resposta = cliente_de_erros.get("/api/v1/_teste/nao-encontrado")

    assert resposta.status_code == 404
    assert resposta.json() == {
        "erro": "enxoval_nao_encontrado",
        "mensagem": "Enxoval não encontrado. Confira o link ou comece um novo.",
    }


def test_dado_invalido_vira_422(cliente_de_erros):
    resposta = cliente_de_erros.get("/api/v1/_teste/invalido")

    assert resposta.status_code == 422
    assert resposta.json() == {"erro": "codigo_qualquer", "mensagem": "Mensagem em português."}


def test_erro_inesperado_vira_500_generico_sem_vazar_detalhe(cliente_de_erros):
    resposta = cliente_de_erros.get("/api/v1/_teste/explode")

    assert resposta.status_code == 500
    assert resposta.json()["erro"] == "erro_interno"
    assert "detalhe interno" not in resposta.text


def test_obter_hoje_devolve_a_data_de_hoje():
    assert obter_hoje() == date.today()


def test_erro_inesperado_nao_vaza_o_uuid_para_o_log(cliente_de_erros, caplog):
    import logging

    uuid_exemplo = "c7ef724d-b37f-4db1-90bf-54fb675a84f7"

    with caplog.at_level(logging.ERROR):
        resposta = cliente_de_erros.get(f"/api/v1/_teste/explode/{uuid_exemplo}")

    assert resposta.status_code == 500
    assert uuid_exemplo not in caplog.text
    assert "[uuid]" in caplog.text
