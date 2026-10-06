import pytest
from sqlalchemy import select

from app.db.catalogo import Estado, FaseRoteiro, PerfilClima
from app.db.enums import PerfilCodigo, Prioridade
from seed.base import carregar_base
from seed.util import enum_de


def test_carga_base_insere_tudo(sessao):
    resumo = carregar_base(sessao)

    assert resumo == {
        "categoria": 7,
        "fase_roteiro": 8,
        "perfil_clima": 3,
        "janela_tamanho": 5,
        "estado": 27,
    }


def test_carga_base_e_idempotente(sessao):
    carregar_base(sessao)

    segunda = carregar_base(sessao)

    assert set(segunda.values()) == {0}


def test_perfis_e_estados_conforme_o_plano(sessao):
    carregar_base(sessao)

    frio = sessao.scalars(
        select(PerfilClima).where(PerfilClima.codigo == PerfilCodigo.FRIO)
    ).one()
    assert frio.meses_frios == [5, 6, 7, 8, 9]
    assert sessao.get(Estado, "PR").perfil_padrao == PerfilCodigo.FRIO
    assert sessao.get(Estado, "BA").perfil_padrao == PerfilCodigo.QUENTE
    assert sessao.get(Estado, "SP").perfil_padrao == PerfilCodigo.MODERADO
    ordens = sessao.scalars(select(FaseRoteiro.codigo).order_by(FaseRoteiro.ordem)).all()
    assert ordens[0] == "gestacao_ate_5m" and ordens[-1] == "bebe_9_12m"


def test_enum_de_explica_o_erro():
    with pytest.raises(ValueError, match="item 'body'.*essencal.*essencial, util, pode_esperar"):
        enum_de(Prioridade, "essencal", "item 'body'")
