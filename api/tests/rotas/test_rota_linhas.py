import uuid

import pytest

CORPO = {
    "municipio_codigo": 4106902,
    "data_prevista": "2027-06-15",
    "dias_entre_lavagens": 2,
    "moradia": "apartamento",
    "tem_carro": True,
    "orcamento": "intermediario",
    "primeiro_filho": True,
}


@pytest.fixture
def enxoval_id(cliente, catalogo_no_banco) -> str:
    return cliente.post("/api/v1/enxovais", json=CORPO).json()["id"]


def _linha(corpo: dict, chave: str) -> dict:
    return next(l for l in corpo["linhas"] if l["chave"] == chave)


def test_marcar_devolve_a_lista_atualizada(cliente, enxoval_id):
    resposta = cliente.put(
        f"/api/v1/enxovais/{enxoval_id}/linhas/body:P:frio",
        json={"comprada": 3, "ganhada": 4, "ja_tinha": 0},
    )

    assert resposta.status_code == 200
    linha = _linha(resposta.json(), "body:P:frio")
    assert (linha["comprada"], linha["ganhada"], linha["faltam"]) == (3, 4, 1)
    assert resposta.json()["progresso"]["atendidas"] == 7


def test_marcar_de_novo_substitui(cliente, enxoval_id):
    cliente.put(
        f"/api/v1/enxovais/{enxoval_id}/linhas/body:P:frio",
        json={"comprada": 3, "ganhada": 4, "ja_tinha": 0},
    )

    corpo = cliente.put(
        f"/api/v1/enxovais/{enxoval_id}/linhas/body:P:frio",
        json={"comprada": 1, "ganhada": 0, "ja_tinha": 0},
    ).json()

    assert _linha(corpo, "body:P:frio")["comprada"] == 1
    assert corpo["progresso"]["atendidas"] == 1


def test_marcar_acima_do_sugerido_e_aceito_e_nao_passa_de_100_por_cento(cliente, enxoval_id):
    corpo = cliente.put(
        f"/api/v1/enxovais/{enxoval_id}/linhas/body:P:frio",
        json={"comprada": 50, "ganhada": 0, "ja_tinha": 0},
    ).json()

    assert _linha(corpo, "body:P:frio")["comprada"] == 50
    assert _linha(corpo, "body:P:frio")["faltam"] == 0
    assert corpo["progresso"]["percentual"] <= 100


def test_marcar_chave_fora_da_lista_guarda_e_devolve_em_fora_da_lista(cliente, enxoval_id):
    corpo = cliente.put(
        f"/api/v1/enxovais/{enxoval_id}/linhas/item-que-nao-existe::",
        json={"comprada": 2, "ganhada": 0, "ja_tinha": 0},
    ).json()

    assert [l["chave"] for l in corpo["linhas_fora_da_lista"]] == ["item-que-nao-existe::"]


@pytest.mark.parametrize(
    "corpo",
    [
        {"comprada": -1, "ganhada": 0, "ja_tinha": 0},
        {"comprada": 0, "ganhada": 0},
        {},
    ],
)
def test_marcacao_invalida_da_422(cliente, enxoval_id, corpo):
    resposta = cliente.put(
        f"/api/v1/enxovais/{enxoval_id}/linhas/body:P:frio", json=corpo
    )

    assert resposta.status_code == 422
    assert resposta.json()["mensagem"]


def test_completar_preenche_o_que_falta(cliente, enxoval_id):
    cliente.put(
        f"/api/v1/enxovais/{enxoval_id}/linhas/body:P:frio",
        json={"comprada": 3, "ganhada": 0, "ja_tinha": 0},
    )

    corpo = cliente.post(
        f"/api/v1/enxovais/{enxoval_id}/linhas/body:P:frio/completar",
        json={"origem": "comprada"},
    ).json()

    linha = _linha(corpo, "body:P:frio")
    assert (linha["comprada"], linha["faltam"]) == (8, 0)


def test_completar_com_ganhada(cliente, enxoval_id):
    corpo = cliente.post(
        f"/api/v1/enxovais/{enxoval_id}/linhas/berco::/completar",
        json={"origem": "ganhada"},
    ).json()

    assert _linha(corpo, "berco::")["ganhada"] == 1


def test_completar_origem_invalida_da_422(cliente, enxoval_id):
    resposta = cliente.post(
        f"/api/v1/enxovais/{enxoval_id}/linhas/body:P:frio/completar",
        json={"origem": "roubada"},
    )

    assert resposta.status_code == 422


def test_completar_linha_inexistente_da_422(cliente, enxoval_id):
    resposta = cliente.post(
        f"/api/v1/enxovais/{enxoval_id}/linhas/nao-existe::/completar",
        json={"origem": "comprada"},
    )

    assert resposta.status_code == 422
    assert resposta.json()["erro"] == "linha_nao_encontrada"


def test_marcar_em_enxoval_inexistente_da_404(cliente, catalogo_no_banco):
    resposta = cliente.put(
        f"/api/v1/enxovais/{uuid.uuid4()}/linhas/body:P:frio",
        json={"comprada": 1, "ganhada": 0, "ja_tinha": 0},
    )

    assert resposta.status_code == 404
    assert resposta.json()["erro"] == "enxoval_nao_encontrado"


def test_item_de_seguranca_pode_ser_marcado_como_qualquer_outro(cliente, enxoval_id):
    corpo = cliente.put(
        f"/api/v1/enxovais/{enxoval_id}/linhas/berco::",
        json={"comprada": 1, "ganhada": 0, "ja_tinha": 0},
    ).json()

    berco = _linha(corpo, "berco::")
    assert berco["e_seguranca"] is True
    assert berco["faltam"] == 0


# ── Hardening: quantidade absurda deve dar 422 (não 500) ──────────────────────

@pytest.mark.parametrize("campo", ["comprada", "ganhada", "ja_tinha"])
def test_quantidade_absurda_da_422(cliente, enxoval_id, campo):
    """Quantidade acima de 9999 deve retornar 422, não 500."""
    corpo = {"comprada": 0, "ganhada": 0, "ja_tinha": 0, campo: 10_000}
    resposta = cliente.put(
        f"/api/v1/enxovais/{enxoval_id}/linhas/body:P:frio", json=corpo
    )
    assert resposta.status_code == 422
    assert resposta.json()["erro"] == "dados_invalidos"
