import pytest


def test_perfis_de_clima(cliente, catalogo_no_banco):
    resposta = cliente.get("/api/v1/perfis-clima")

    assert resposta.status_code == 200
    perfis = {p["codigo"]: p for p in resposta.json()}
    assert set(perfis) == {"quente", "moderado", "frio"}
    assert perfis["frio"]["meses_frios"] == [5, 6, 7, 8, 9]
    assert perfis["quente"]["meses_frescos"] == [6, 7]
    assert "Frio de maio a setembro" in perfis["frio"]["descricao"]


@pytest.mark.parametrize(
    ("busca", "esperado"),
    [
        ("curitiba", "Curitiba"),
        ("CURITIBA", "Curitiba"),
        ("Curitíba", "Curitiba"),       # acento a mais
        ("sao paulo", "São Paulo"),
        ("são paulo", "São Paulo"),
        ("sao pau", "São Paulo"),
        ("alta floresta d", "Alta Floresta D'Oeste"),
        ("alta floresta d'o", "Alta Floresta D'Oeste"),
        ("alta floresta d’o", "Alta Floresta D'Oeste"),
        ("salvador", "Salvador"),
    ],
)
def test_busca_acha_a_cidade(cliente, catalogo_no_banco, busca, esperado):
    resposta = cliente.get("/api/v1/municipios", params={"busca": busca})

    assert resposta.status_code == 200
    assert esperado in [m["nome"] for m in resposta.json()]


def test_busca_traz_o_perfil_sugerido(cliente, catalogo_no_banco):
    curitiba = cliente.get("/api/v1/municipios", params={"busca": "curitiba"}).json()[0]
    sao_paulo = cliente.get("/api/v1/municipios", params={"busca": "sao paulo"}).json()[0]

    assert curitiba["perfil_sugerido"] == "frio"      # padrão do Paraná
    assert sao_paulo["perfil_sugerido"] == "moderado"  # padrão de São Paulo


def test_excecao_do_municipio_aparece_no_perfil_sugerido(cliente, catalogo_no_banco):
    resultados = cliente.get("/api/v1/municipios", params={"busca": "bom jesus"}).json()

    por_uf = {m["uf"]: m["perfil_sugerido"] for m in resultados}
    assert por_uf["RS"] == "moderado"  # exceção cadastrada (o padrão do RS é frio)
    assert por_uf["PI"] == "quente"  # padrão do Piauí


def test_homonimos_vem_os_dois_com_a_uf(cliente, catalogo_no_banco):
    resultados = cliente.get("/api/v1/municipios", params={"busca": "bom jesus"}).json()

    assert sorted(m["uf"] for m in resultados) == ["PI", "RS"]


@pytest.mark.parametrize("busca", ["", " ", "a", "-", "'"])
def test_busca_curta_nao_devolve_a_tabela_inteira(cliente, catalogo_no_banco, busca):
    resposta = cliente.get("/api/v1/municipios", params={"busca": busca})

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_busca_sem_resultado_devolve_lista_vazia(cliente, catalogo_no_banco):
    resposta = cliente.get("/api/v1/municipios", params={"busca": "cidade inventada"})

    assert resposta.status_code == 200
    assert resposta.json() == []


def test_busca_limita_a_dez_resultados(cliente, catalogo_no_banco):
    from app.db.catalogo import Municipio
    from app.texto import normalizar_busca

    for i in range(15):
        nome = f"Vila Teste {i}"
        catalogo_no_banco.add(
            Municipio(
                codigo_ibge=8000000 + i, nome=nome,
                nome_busca=normalizar_busca(nome), uf="PR",
            )
        )
    catalogo_no_banco.flush()

    resultados = cliente.get("/api/v1/municipios", params={"busca": "vila teste"}).json()

    assert len(resultados) == 10


def test_busca_sem_o_parametro_e_erro_de_validacao(cliente, catalogo_no_banco):
    resposta = cliente.get("/api/v1/municipios")

    assert resposta.status_code == 422
    assert resposta.json()["erro"] == "dados_invalidos"


def test_correspondencia_exata_aparece_mesmo_com_dez_prefixos_antes_na_ordem_alfabetica(
    cliente, catalogo_no_banco
):
    """Serra/ES existe de verdade e some do resultado se 'Amparo do Serra' etc.

    ficarem antes dela na ordenação alfabética e empurrarem o LIMIT 10."""
    from app.db.catalogo import Municipio
    from app.texto import normalizar_busca

    nome_exato = "Serra"
    catalogo_no_banco.add(
        Municipio(
            codigo_ibge=9000000, nome=nome_exato,
            nome_busca=normalizar_busca(nome_exato), uf="ES",
        )
    )
    for i in range(12):
        nome = f"Amparo {i} da Serra"
        catalogo_no_banco.add(
            Municipio(
                codigo_ibge=9000001 + i, nome=nome,
                nome_busca=normalizar_busca(nome), uf="MG",
            )
        )
    catalogo_no_banco.flush()

    resultados = cliente.get("/api/v1/municipios", params={"busca": "serra"}).json()

    assert nome_exato in [m["nome"] for m in resultados]
