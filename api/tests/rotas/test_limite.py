import pytest

from app.erros import ErroDominio
from app.limite import LimitePorIp

CORPO = {
    "municipio_codigo": 4106902,
    "data_prevista": "2027-06-15",
    "dias_entre_lavagens": 2,
    "moradia": "apartamento",
    "tem_carro": True,
    "orcamento": "intermediario",
    "primeiro_filho": True,
}


def test_limite_deixa_passar_ate_o_maximo():
    limite = LimitePorIp(maximo=3, janela_segundos=60)

    for i in range(3):
        limite.verificar("1.2.3.4", agora=100.0 + i)

    with pytest.raises(ErroDominio) as erro:
        limite.verificar("1.2.3.4", agora=103.0)
    assert erro.value.status == 429
    assert erro.value.codigo == "muitas_requisicoes"


def test_limite_e_por_ip():
    limite = LimitePorIp(maximo=1, janela_segundos=60)
    limite.verificar("1.1.1.1", agora=0.0)

    limite.verificar("2.2.2.2", agora=0.0)  # não levanta


def test_janela_expira():
    limite = LimitePorIp(maximo=1, janela_segundos=60)
    limite.verificar("1.1.1.1", agora=0.0)

    limite.verificar("1.1.1.1", agora=61.0)  # não levanta


def test_criacao_em_excesso_responde_429(cliente, catalogo_no_banco, monkeypatch):
    from app.rotas import enxovais

    monkeypatch.setattr(enxovais, "limite_de_criacao", LimitePorIp(maximo=2, janela_segundos=3600))

    assert cliente.post("/api/v1/enxovais", json=CORPO).status_code == 201
    assert cliente.post("/api/v1/enxovais", json=CORPO).status_code == 201
    resposta = cliente.post("/api/v1/enxovais", json=CORPO)

    assert resposta.status_code == 429
    assert resposta.json()["erro"] == "muitas_requisicoes"
    assert "Tente de novo" in resposta.json()["mensagem"]
