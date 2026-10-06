import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.db.catalogo import Categoria, FaseRoteiro, Item, ItemRegra, JanelaTamanho
from app.db.enums import Condicao, Efeito, Prioridade, ReferenciaFase, Tamanho


@pytest.fixture
def item(sessao) -> Item:
    categoria = Categoria(slug="c", nome="C", ordem=1)
    fase = FaseRoteiro(
        codigo="f", nome="F", referencia=ReferenciaFase.BEBE_MES,
        inicio=0, fim=2, texto="t", ordem=1,
    )
    sessao.add_all([categoria, fase])
    sessao.flush()
    item = Item(
        slug="x", nome="X", categoria=categoria, fase_compra=fase,
        prioridade_base=Prioridade.UTIL, para_que_serve="a", como_escolher="b", quantidade=1,
    )
    sessao.add(item)
    sessao.flush()
    return item


@pytest.mark.parametrize(("inicio", "fim"), [(90, 90), (90, 30)])
def test_janela_sem_duracao_e_recusada(sessao, inicio, fim):
    sessao.add(JanelaTamanho(tamanho=Tamanho.P, idade_inicio_dias=inicio, idade_fim_dias=fim))
    with pytest.raises(IntegrityError):
        sessao.flush()


def test_janela_valida_e_aceita(sessao):
    sessao.add(JanelaTamanho(tamanho=Tamanho.P, idade_inicio_dias=0, idade_fim_dias=90))
    sessao.flush()  # não levanta


def test_regra_de_prioridade_com_valor_invalido_e_recusada(sessao, item):
    sessao.add(
        ItemRegra(
            item=item, condicao=Condicao.SEM_CARRO,
            efeito=Efeito.MUDAR_PRIORIDADE, valor="essencal",
        )
    )
    with pytest.raises(IntegrityError):
        sessao.flush()


def test_regra_de_prioridade_sem_valor_e_recusada(sessao, item):
    sessao.add(
        ItemRegra(item=item, condicao=Condicao.SEM_CARRO, efeito=Efeito.MUDAR_PRIORIDADE)
    )
    with pytest.raises(IntegrityError):
        sessao.flush()


def test_dica_com_texto_livre_continua_aceita(sessao, item):
    sessao.add(
        ItemRegra(
            item=item, condicao=Condicao.APARTAMENTO, efeito=Efeito.DICA,
            valor="Qualquer texto, com vírgula e tudo.",
        )
    )
    sessao.flush()  # não levanta


def test_incluir_so_se_sem_valor_continua_aceita(sessao, item):
    sessao.add(
        ItemRegra(item=item, condicao=Condicao.CASA_COM_ESCADA, efeito=Efeito.INCLUIR_SO_SE)
    )
    sessao.flush()  # não levanta


def test_nomes_das_travas_seguem_a_convencao_do_projeto(sessao):
    """A migração não pode duplicar o prefixo (ck_<tabela>_ck_<tabela>_...)."""
    conexao = sessao.connection()
    nomes = {
        r[0]
        for r in conexao.execute(
            text(
                "SELECT conname FROM pg_constraint "
                "WHERE conname IN ("
                "'ck_janela_tamanho_janela_com_duracao', "
                "'ck_item_regra_valor_de_prioridade_valido'"
                ")"
            )
        )
    }
    assert nomes == {
        "ck_janela_tamanho_janela_com_duracao",
        "ck_item_regra_valor_de_prioridade_valido",
    }
