import uuid

import pytest

CORPO = {
    "municipio_codigo": 4106902,  # Curitiba
    "data_prevista": "2027-06-15",
    "dias_entre_lavagens": 2,
    "moradia": "apartamento",
    "tem_carro": True,
    "orcamento": "intermediario",
    "primeiro_filho": True,
}


def _criar(cliente, **extra) -> str:
    resposta = cliente.post("/api/v1/enxovais", json={**CORPO, **extra})
    assert resposta.status_code == 201, resposta.text
    return resposta.json()["id"]


def test_criar_devolve_201_com_id_e_location(cliente, catalogo_no_banco):
    resposta = cliente.post("/api/v1/enxovais", json=CORPO)

    assert resposta.status_code == 201
    identificador = resposta.json()["id"]
    assert uuid.UUID(identificador)
    assert resposta.headers["Location"] == f"/api/v1/enxovais/{identificador}"


def test_ler_traz_a_lista_calculada_de_curitiba(cliente, catalogo_no_banco):
    identificador = _criar(cliente)

    corpo = cliente.get(f"/api/v1/enxovais/{identificador}").json()

    assert corpo["respostas"]["municipio"]["nome"] == "Curitiba"
    assert corpo["respostas"]["perfil_clima"] == "frio"
    linhas = {l["chave"]: l for l in corpo["linhas"]}
    assert linhas["body:P:frio"]["quantidade"] == 8
    assert linhas["body:P:frio"]["rotulo_variante"] == "manga longa"
    assert linhas["body:P:frio"]["faltam"] == 8
    assert "body:P:calor" not in linhas
    assert len(corpo["roteiro"]) == 8
    assert len(corpo["alertas"]) == 8
    assert len(corpo["categorias"]) == 7
    assert corpo["resumo"]["dias_sem_lavar"] == 2
    assert corpo["progresso"]["percentual"] == 0
    assert corpo["linhas_fora_da_lista"] == []
    assert "avisos" not in corpo


def test_ficha_vem_com_marcas_e_seguranca(cliente, catalogo_no_banco):
    identificador = _criar(cliente)

    corpo = cliente.get(f"/api/v1/enxovais/{identificador}").json()

    berco = next(f for f in corpo["fichas"] if f["slug"] == "berco")
    assert berco["marcas"]["nomes"][:2] == ["Tcil", "Reller"]
    assert berco["marcas"]["faixa_aproximada"] is False
    assert "sono-seguro" in berco["regras_seguranca"]
    manta = next(f for f in corpo["fichas"] if f["slug"] == "manta")
    assert manta["marcas"]["faixa_aproximada"] is True


def test_cabecalhos_de_privacidade_na_leitura(cliente, catalogo_no_banco):
    identificador = _criar(cliente)

    resposta = cliente.get(f"/api/v1/enxovais/{identificador}")

    assert resposta.headers["Referrer-Policy"] == "no-referrer"
    assert resposta.headers["X-Robots-Tag"] == "noindex"


def test_editar_respostas_recalcula_a_lista(cliente, catalogo_no_banco):
    identificador = _criar(cliente)

    resposta = cliente.patch(
        f"/api/v1/enxovais/{identificador}",
        json={**CORPO, "municipio_codigo": 2927408},  # Salvador
    )

    assert resposta.status_code == 200
    corpo = resposta.json()
    assert corpo["respostas"]["perfil_clima"] == "quente"
    linhas = {l["chave"] for l in corpo["linhas"]}
    assert "body:P:calor" in linhas
    assert not [c for c in linhas if c.startswith("gorro")]


def test_correcao_de_perfil_e_registrada(cliente, catalogo_no_banco):
    identificador = _criar(cliente, correcao_perfil="quente")

    corpo = cliente.get(f"/api/v1/enxovais/{identificador}").json()

    assert corpo["respostas"]["perfil_clima"] == "quente"
    assert corpo["respostas"]["perfil_corrigido"] is True


def test_apagar_devolve_204_e_a_leitura_passa_a_dar_404(cliente, catalogo_no_banco):
    identificador = _criar(cliente)

    assert cliente.delete(f"/api/v1/enxovais/{identificador}").status_code == 204
    assert cliente.get(f"/api/v1/enxovais/{identificador}").status_code == 404


def test_uuid_inexistente_da_404_em_portugues(cliente, catalogo_no_banco):
    resposta = cliente.get(f"/api/v1/enxovais/{uuid.uuid4()}")

    assert resposta.status_code == 404
    assert resposta.json()["erro"] == "enxoval_nao_encontrado"
    assert "Confira o link" in resposta.json()["mensagem"]


@pytest.mark.parametrize("identificador", ["nao-e-uuid", "123", "0b7f-xx"])
def test_uuid_malformado_da_422_e_nao_500(cliente, catalogo_no_banco, identificador):
    resposta = cliente.get(f"/api/v1/enxovais/{identificador}")

    assert resposta.status_code == 422
    assert resposta.json()["erro"] == "dados_invalidos"


@pytest.mark.parametrize(
    ("campo", "valor"),
    [
        ("data_prevista", "2026-01-01"),   # mais de um ano atrás
        ("data_prevista", "2027-12-02"),   # mais de 10 meses à frente
        ("data_prevista", "2027-02-30"),   # dia que não existe
        ("data_prevista", "ontem"),
        ("dias_entre_lavagens", 0),
        ("dias_entre_lavagens", 8),
        ("moradia", "barco"),
        ("orcamento", "rico"),
        ("municipio_codigo", 0),
    ],
)
def test_resposta_invalida_da_422(cliente, catalogo_no_banco, campo, valor):
    resposta = cliente.post("/api/v1/enxovais", json={**CORPO, campo: valor})

    assert resposta.status_code == 422, resposta.text
    assert resposta.json()["erro"] in (
        "dados_invalidos", "data_prevista_fora_da_faixa", "data_prevista_invalida",
    )
    assert resposta.json()["mensagem"]


@pytest.mark.parametrize("valor", ["2027-02-30", "2027-02-29", "ontem", "15/06/2027"])
def test_data_prevista_malformada_diz_o_formato_aceito(cliente, catalogo_no_banco, valor):
    """2027 não é bissexto, então 29 e 30/02 não existem; a mensagem genérica
    não dizia nem o campo nem o formato aceito (Review Focus 4)."""
    resposta = cliente.post("/api/v1/enxovais", json={**CORPO, "data_prevista": valor})

    assert resposta.status_code == 422, resposta.text
    assert resposta.json()["erro"] == "data_prevista_invalida"
    assert "AAAA-MM-DD" in resposta.json()["mensagem"]


def test_cidade_inexistente_da_422_com_codigo_proprio(cliente, catalogo_no_banco):
    resposta = cliente.post("/api/v1/enxovais", json={**CORPO, "municipio_codigo": 999})

    assert resposta.status_code == 422
    assert resposta.json()["erro"] == "municipio_nao_encontrado"


def test_banco_sem_catalogo_responde_lista_vazia_e_nao_500(cliente, sessao):
    from app.db.catalogo import Estado, Municipio
    from app.db.enums import PerfilCodigo
    from app.texto import normalizar_busca

    sessao.add(Estado(uf="PR", nome="Paraná", perfil_padrao=PerfilCodigo.FRIO))
    sessao.add(
        Municipio(
            codigo_ibge=4106902, nome="Curitiba",
            nome_busca=normalizar_busca("Curitiba"), uf="PR",
        )
    )
    sessao.flush()

    identificador = _criar(cliente)
    corpo = cliente.get(f"/api/v1/enxovais/{identificador}").json()

    assert corpo["linhas"] == []
    assert corpo["progresso"]["total_unidades"] == 0
