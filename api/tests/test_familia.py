from datetime import date

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError

from app.db.catalogo import Estado, Municipio
from app.db.enums import Faixa, Moradia, PerfilCodigo
from app.db.familia import Enxoval, EnxovalLinha


@pytest.fixture
def curitiba(sessao):
    sessao.add(Estado(uf="PR", nome="Paraná", perfil_padrao=PerfilCodigo.FRIO))
    municipio = Municipio(
        codigo_ibge=4106902, nome="Curitiba", nome_busca="curitiba", uf="PR"
    )
    sessao.add(municipio)
    sessao.flush()
    return municipio


def _enxoval(municipio, **extra):
    dados = dict(
        municipio_codigo=municipio.codigo_ibge,
        perfil_clima=PerfilCodigo.FRIO,
        data_prevista=date(2027, 6, 15),
        dias_entre_lavagens=2,
        moradia=Moradia.APARTAMENTO,
        tem_carro=True,
        orcamento=Faixa.INTERMEDIARIO,
        primeiro_filho=True,
    )
    dados.update(extra)
    return Enxoval(**dados)


def test_enxoval_recebe_uuid_e_datas(sessao, curitiba):
    enxoval = _enxoval(curitiba)
    sessao.add(enxoval)
    sessao.flush()
    sessao.refresh(enxoval)

    assert len(str(enxoval.id)) == 36
    assert enxoval.criado_em is not None
    assert enxoval.perfil_corrigido is False


def test_apagar_enxoval_apaga_as_linhas(sessao, curitiba):
    enxoval = _enxoval(curitiba)
    enxoval.linhas.append(EnxovalLinha(chave="body:P:frio", qtd_comprada=3))
    sessao.add(enxoval)
    sessao.flush()

    sessao.delete(enxoval)
    sessao.flush()

    assert sessao.scalar(select(func.count()).select_from(EnxovalLinha)) == 0


def test_linha_comeca_zerada(sessao, curitiba):
    enxoval = _enxoval(curitiba)
    enxoval.linhas.append(EnxovalLinha(chave="berco::"))
    sessao.add(enxoval)
    sessao.flush()

    linha = enxoval.linhas[0]
    assert (linha.qtd_comprada, linha.qtd_ganhada, linha.qtd_ja_tinha) == (0, 0, 0)


@pytest.mark.parametrize("dias", [0, 8])
def test_dias_entre_lavagens_fora_de_1_a_7_e_recusado(sessao, curitiba, dias):
    sessao.add(_enxoval(curitiba, dias_entre_lavagens=dias))
    with pytest.raises(IntegrityError):
        sessao.flush()


def test_quantidade_negativa_e_recusada(sessao, curitiba):
    enxoval = _enxoval(curitiba)
    enxoval.linhas.append(EnxovalLinha(chave="body:P:frio", qtd_ganhada=-1))
    sessao.add(enxoval)
    with pytest.raises(IntegrityError):
        sessao.flush()
