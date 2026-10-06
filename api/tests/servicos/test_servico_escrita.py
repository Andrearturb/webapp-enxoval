import uuid
from datetime import date, timedelta

import pytest

from app.db.enums import Faixa, Moradia, PerfilCodigo
from app.db.familia import Enxoval, EnxovalLinha
from app.erros import DadoInvalido, EnxovalNaoEncontrado
from app.servicos.escrita import (
    DadosRespostas,
    apagar_enxoval,
    completar_linha,
    criar_enxoval,
    editar_respostas,
    marcar_linha,
)
from app.servicos.leitura import ler_enxoval

HOJE = date(2027, 2, 1)
DPP = date(2027, 6, 15)


def _dados(**extra) -> DadosRespostas:
    base = dict(
        municipio_codigo=4106902,  # Curitiba
        data_prevista=DPP,
        dias_entre_lavagens=2,
        moradia=Moradia.APARTAMENTO,
        tem_carro=True,
        orcamento=Faixa.INTERMEDIARIO,
        primeiro_filho=True,
    )
    base.update(extra)
    return DadosRespostas(**base)


def test_criar_resolve_o_perfil_pelo_estado(catalogo_no_banco):
    enxoval = criar_enxoval(catalogo_no_banco, _dados(), HOJE)

    assert enxoval.perfil_clima == PerfilCodigo.FRIO  # Paraná
    assert enxoval.perfil_corrigido is False
    assert isinstance(enxoval.id, uuid.UUID)


def test_criar_usa_a_excecao_do_municipio(catalogo_no_banco):
    # Bom Jesus/RS tem exceção "moderado", diferente do padrão do estado (frio)
    enxoval = criar_enxoval(catalogo_no_banco, _dados(municipio_codigo=4302105), HOJE)

    assert enxoval.perfil_clima == PerfilCodigo.MODERADO


def test_correcao_da_familia_vence_e_fica_registrada(catalogo_no_banco):
    enxoval = criar_enxoval(
        catalogo_no_banco, _dados(correcao_perfil=PerfilCodigo.QUENTE), HOJE
    )

    assert enxoval.perfil_clima == PerfilCodigo.QUENTE
    assert enxoval.perfil_corrigido is True


def test_municipio_inexistente_e_recusado(catalogo_no_banco):
    with pytest.raises(DadoInvalido) as erro:
        criar_enxoval(catalogo_no_banco, _dados(municipio_codigo=1), HOJE)

    assert erro.value.codigo == "municipio_nao_encontrado"


@pytest.mark.parametrize(
    "data_prevista",
    [date(2026, 1, 31), date(2027, 12, 2), date(2030, 1, 1)],
)
def test_data_prevista_fora_da_faixa_e_recusada(catalogo_no_banco, data_prevista):
    with pytest.raises(DadoInvalido) as erro:
        criar_enxoval(catalogo_no_banco, _dados(data_prevista=data_prevista), HOJE)

    assert erro.value.codigo == "data_prevista_fora_da_faixa"
    assert "10 meses" in erro.value.mensagem


@pytest.mark.parametrize(
    "data_prevista", [date(2026, 2, 1), HOJE, date(2027, 12, 1)]
)
def test_limites_da_faixa_de_data_sao_aceitos(catalogo_no_banco, data_prevista):
    enxoval = criar_enxoval(catalogo_no_banco, _dados(data_prevista=data_prevista), HOJE)

    assert enxoval.data_prevista == data_prevista


def test_editar_respostas_troca_a_lista_e_preserva_marcacoes(catalogo_no_banco):
    enxoval = criar_enxoval(catalogo_no_banco, _dados(), HOJE)
    marcar_linha(catalogo_no_banco, enxoval.id, "gorro:P:", comprada=2, ganhada=0, ja_tinha=0)

    editar_respostas(
        catalogo_no_banco, enxoval.id, _dados(municipio_codigo=2927408), HOJE  # Salvador
    )
    completo = ler_enxoval(catalogo_no_banco, enxoval.id, HOJE)

    assert completo.enxoval.perfil_clima == PerfilCodigo.QUENTE
    assert "gorro:P:" not in {l.chave for l in completo.calculado.linhas}
    assert [l.chave for l in completo.fora_da_lista] == ["gorro:P:"]


def test_marcar_linha_grava_e_atualiza(catalogo_no_banco):
    enxoval = criar_enxoval(catalogo_no_banco, _dados(), HOJE)

    linha = marcar_linha(catalogo_no_banco, enxoval.id, "body:P:frio", 3, 4, 0)
    assert (linha.qtd_comprada, linha.qtd_ganhada, linha.qtd_ja_tinha) == (3, 4, 0)

    linha = marcar_linha(catalogo_no_banco, enxoval.id, "body:P:frio", 5, 0, 1)
    assert (linha.qtd_comprada, linha.qtd_ganhada, linha.qtd_ja_tinha) == (5, 0, 1)
    assert catalogo_no_banco.query(EnxovalLinha).count() == 1


def test_marcar_aceita_chave_fora_da_lista_atual(catalogo_no_banco):
    """Perder o que a família marcou é pior do que guardar uma chave órfã."""
    enxoval = criar_enxoval(catalogo_no_banco, _dados(municipio_codigo=2927408), HOJE)

    linha = marcar_linha(catalogo_no_banco, enxoval.id, "gorro:P:", 1, 0, 0)

    assert linha.qtd_comprada == 1


def test_marcar_acima_do_sugerido_e_permitido(catalogo_no_banco):
    enxoval = criar_enxoval(catalogo_no_banco, _dados(), HOJE)

    linha = marcar_linha(catalogo_no_banco, enxoval.id, "body:P:frio", 0, 20, 0)

    assert linha.qtd_ganhada == 20


@pytest.mark.parametrize(("c", "g", "j"), [(-1, 0, 0), (0, -2, 0), (0, 0, -1)])
def test_marcar_com_negativo_e_recusado(catalogo_no_banco, c, g, j):
    enxoval = criar_enxoval(catalogo_no_banco, _dados(), HOJE)

    with pytest.raises(DadoInvalido) as erro:
        marcar_linha(catalogo_no_banco, enxoval.id, "body:P:frio", c, g, j)

    assert erro.value.codigo == "quantidade_negativa"


def test_completar_preenche_o_que_falta(catalogo_no_banco):
    enxoval = criar_enxoval(catalogo_no_banco, _dados(), HOJE)
    marcar_linha(catalogo_no_banco, enxoval.id, "body:P:frio", 3, 0, 0)

    linha = completar_linha(catalogo_no_banco, enxoval.id, "body:P:frio", "comprada", HOJE)

    assert linha.qtd_comprada == 8  # a linha pede 8
    assert linha.qtd_ganhada == 0


def test_completar_nao_reduz_quem_ja_passou(catalogo_no_banco):
    enxoval = criar_enxoval(catalogo_no_banco, _dados(), HOJE)
    marcar_linha(catalogo_no_banco, enxoval.id, "body:P:frio", 0, 12, 0)

    linha = completar_linha(catalogo_no_banco, enxoval.id, "body:P:frio", "comprada", HOJE)

    assert (linha.qtd_comprada, linha.qtd_ganhada) == (0, 12)


def test_completar_linha_inexistente_e_recusado(catalogo_no_banco):
    enxoval = criar_enxoval(catalogo_no_banco, _dados(), HOJE)

    with pytest.raises(DadoInvalido) as erro:
        completar_linha(catalogo_no_banco, enxoval.id, "nao-existe::", "comprada", HOJE)

    assert erro.value.codigo == "linha_nao_encontrada"


def test_completar_com_origem_invalida_e_recusado(catalogo_no_banco):
    enxoval = criar_enxoval(catalogo_no_banco, _dados(), HOJE)

    with pytest.raises(DadoInvalido) as erro:
        completar_linha(catalogo_no_banco, enxoval.id, "body:P:frio", "roubada", HOJE)

    assert erro.value.codigo == "origem_invalida"


def test_apagar_leva_as_linhas(catalogo_no_banco):
    enxoval = criar_enxoval(catalogo_no_banco, _dados(), HOJE)
    marcar_linha(catalogo_no_banco, enxoval.id, "body:P:frio", 1, 0, 0)
    enxoval_id = enxoval.id

    apagar_enxoval(catalogo_no_banco, enxoval_id)

    assert catalogo_no_banco.query(Enxoval).count() == 0
    assert catalogo_no_banco.query(EnxovalLinha).count() == 0
    with pytest.raises(EnxovalNaoEncontrado):
        ler_enxoval(catalogo_no_banco, enxoval_id, HOJE)


def test_operacoes_em_enxoval_inexistente_levantam_nao_encontrado(catalogo_no_banco):
    inexistente = uuid.uuid4()

    for chamada in (
        lambda: editar_respostas(catalogo_no_banco, inexistente, _dados(), HOJE),
        lambda: marcar_linha(catalogo_no_banco, inexistente, "a::", 1, 0, 0),
        lambda: completar_linha(catalogo_no_banco, inexistente, "a::", "comprada", HOJE),
        lambda: apagar_enxoval(catalogo_no_banco, inexistente),
    ):
        with pytest.raises(EnxovalNaoEncontrado):
            chamada()
