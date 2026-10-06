import asyncio

import pytest

from app.admin import MunicipioAdmin
from app.db.catalogo import Estado, Municipio
from app.db.enums import PerfilCodigo


@pytest.fixture
def municipio(sessao) -> Municipio:
    sessao.add(Estado(uf="PR", nome="Paraná", perfil_padrao=PerfilCodigo.FRIO))
    municipio = Municipio(
        codigo_ibge=4106902, nome="Curitiba", nome_busca="curitiba", uf="PR"
    )
    sessao.add(municipio)
    sessao.flush()
    return municipio


def test_renomear_no_admin_recalcula_o_nome_de_busca(sessao, municipio):
    municipio.nome = "Curitiba D'Oeste"

    asyncio.run(MunicipioAdmin().on_model_change({}, municipio, False, None))

    assert municipio.nome_busca == "curitiba d oeste"


def test_criar_no_admin_preenche_o_nome_de_busca(sessao):
    novo = Municipio(codigo_ibge=9999999, nome="Vila Nova São José", uf="PR")

    asyncio.run(MunicipioAdmin().on_model_change({}, novo, True, None))

    assert novo.nome_busca == "vila nova sao jose"
