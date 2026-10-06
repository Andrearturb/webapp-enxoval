import pytest
from sqlalchemy import func, select

from app.db.catalogo import Municipio
from app.db.enums import PerfilCodigo
from seed.base import carregar_base
from seed.cidades import aplicar_excecoes, carregar_municipios, normalizar_busca


@pytest.fixture
def cidades(sessao):
    carregar_base(sessao)
    carregar_municipios(sessao)
    aplicar_excecoes(sessao)
    return sessao


def _municipio(sessao, nome, uf) -> Municipio:
    return sessao.scalars(
        select(Municipio).where(Municipio.nome == nome, Municipio.uf == uf)
    ).one()


@pytest.mark.parametrize(
    ("entrada", "esperado"),
    [
        ("São João d'Aliança", "sao joao d alianca"),
        ("  Florianópolis ", "florianopolis"),
        ("SAO   PAULO", "sao paulo"),
    ],
)
def test_normalizar_busca(entrada, esperado):
    assert normalizar_busca(entrada) == esperado


def test_carrega_todos_os_municipios(cidades):
    total = cidades.scalar(select(func.count()).select_from(Municipio))
    assert 5560 <= total <= 5600
    assert _municipio(cidades, "São Paulo", "SP").nome_busca == "sao paulo"


def test_excecoes_de_serra(cidades):
    assert _municipio(cidades, "Campos do Jordão", "SP").perfil_excecao == PerfilCodigo.FRIO
    assert _municipio(cidades, "Garanhuns", "PE").perfil_excecao == PerfilCodigo.MODERADO
    assert _municipio(cidades, "Curitiba", "PR").perfil_excecao is None


def test_excecao_acerta_so_a_uf_informada(cidades):
    homonimos = cidades.scalars(
        select(Municipio).where(Municipio.nome_busca == "bom jesus")
    ).all()
    assert len(homonimos) > 1

    aplicar_excecoes(cidades, [{"nome": "Bom Jesus", "uf": "RS", "perfil": "frio"}])

    marcados = {m.uf for m in homonimos if m.perfil_excecao is not None}
    assert marcados == {"RS"}


def test_excecao_de_municipio_inexistente_e_recusada(cidades):
    with pytest.raises(ValueError, match="Cidade Inventada/SP.*não encontrado"):
        aplicar_excecoes(cidades, [{"nome": "Cidade Inventada", "uf": "SP", "perfil": "frio"}])


def test_carga_de_municipios_e_idempotente(cidades):
    assert carregar_municipios(cidades) == 0
