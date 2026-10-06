from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError

from app.db.sessao import obter_sessao
from app.main import criar_app


def _cliente_com_sessao(sessao) -> TestClient:
    app = criar_app()
    app.dependency_overrides[obter_sessao] = lambda: sessao
    return TestClient(app)


def test_saude_responde_ok_com_banco(sessao):
    resposta = _cliente_com_sessao(sessao).get("/api/v1/saude")

    assert resposta.status_code == 200
    assert resposta.json() == {"status": "ok", "banco": "ok"}


class _SessaoForaDoAr:
    def execute(self, *args, **kwargs):
        raise OperationalError("SELECT 1", {}, Exception("conexão recusada"))


def test_saude_responde_503_sem_banco():
    resposta = _cliente_com_sessao(_SessaoForaDoAr()).get("/api/v1/saude")

    assert resposta.status_code == 503
    assert resposta.json() == {"status": "erro", "banco": "indisponivel"}
