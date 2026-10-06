import uuid
from datetime import date

import pytest

from app.db.enums import Faixa, Moradia, PerfilCodigo
from app.db.familia import Enxoval, EnxovalLinha
from app.erros import EnxovalNaoEncontrado
from app.motor.progresso import Marcacao
from app.servicos.leitura import ler_enxoval

HOJE = date(2027, 2, 1)
DPP = date(2027, 6, 15)


def _criar(sessao, **extra) -> Enxoval:
    dados = dict(
        municipio_codigo=4106902,  # Curitiba
        perfil_clima=PerfilCodigo.FRIO,
        data_prevista=DPP,
        dias_entre_lavagens=2,
        moradia=Moradia.APARTAMENTO,
        tem_carro=True,
        orcamento=Faixa.INTERMEDIARIO,
        primeiro_filho=True,
    )
    dados.update(extra)
    enxoval = Enxoval(**dados)
    sessao.add(enxoval)
    sessao.flush()
    return enxoval


def test_le_o_enxoval_calculado_de_curitiba(catalogo_no_banco):
    enxoval = _criar(catalogo_no_banco)

    completo = ler_enxoval(catalogo_no_banco, enxoval.id, HOJE)

    linhas = {l.chave: l for l in completo.calculado.linhas}
    assert linhas["body:P:frio"].quantidade == 8
    assert "body:P:calor" not in linhas
    assert len(completo.calculado.roteiro) == 8
    assert [f.codigo for f in completo.calculado.roteiro if f.atual] == ["gestacao_5_7m"]
    assert len(completo.calculado.alertas) == 8
    assert completo.calculado.resumo.dias_sem_lavar == 2
    assert completo.calculado.avisos == ()


def test_le_salvador_com_o_perfil_quente(catalogo_no_banco):
    enxoval = _criar(catalogo_no_banco, municipio_codigo=2927408, perfil_clima=PerfilCodigo.QUENTE)

    completo = ler_enxoval(catalogo_no_banco, enxoval.id, HOJE)

    linhas = {l.chave: l for l in completo.calculado.linhas}
    assert linhas["body:P:frio"].quantidade == 2
    assert linhas["body:P:calor"].quantidade == 6
    assert "mosquiteiro::" in linhas


def test_marcacoes_entram_no_progresso(catalogo_no_banco):
    enxoval = _criar(catalogo_no_banco)
    enxoval.linhas.append(EnxovalLinha(chave="body:P:frio", qtd_comprada=3, qtd_ganhada=4))
    enxoval.linhas.append(EnxovalLinha(chave="berco::", qtd_ja_tinha=1))
    catalogo_no_banco.flush()

    completo = ler_enxoval(catalogo_no_banco, enxoval.id, HOJE)

    assert completo.marcadas["body:P:frio"] == Marcacao(comprada=3, ganhada=4, ja_tinha=0)
    assert completo.progresso.atendidas == 8  # 7 do body + 1 do berço
    assert completo.progresso.faltam == completo.progresso.total_unidades - 8
    assert completo.fora_da_lista == ()


def test_linha_que_saiu_da_lista_continua_visivel(catalogo_no_banco):
    """A família trocou de cidade; a chave antiga não é mais calculada, mas foi marcada."""
    enxoval = _criar(catalogo_no_banco, perfil_clima=PerfilCodigo.QUENTE)
    enxoval.linhas.append(EnxovalLinha(chave="gorro:P:", qtd_comprada=2))
    enxoval.linhas.append(EnxovalLinha(chave="saco-dormir::", qtd_ganhada=0))  # zerada: ignorar
    catalogo_no_banco.flush()

    completo = ler_enxoval(catalogo_no_banco, enxoval.id, HOJE)

    assert [l.chave for l in completo.fora_da_lista] == ["gorro:P:"]
    assert completo.progresso.fora_da_lista == ("gorro:P:",)


def test_enxoval_inexistente_levanta_erro_de_dominio(catalogo_no_banco):
    with pytest.raises(EnxovalNaoEncontrado) as erro:
        ler_enxoval(catalogo_no_banco, uuid.uuid4(), HOJE)

    assert erro.value.codigo == "enxoval_nao_encontrado"
    assert "não encontrado" in erro.value.mensagem


def test_banco_sem_seed_devolve_lista_vazia_sem_quebrar(sessao, caplog):
    import logging

    from app.db.catalogo import Estado, Municipio
    from app.db.enums import PerfilCodigo as PC

    sessao.add(Estado(uf="PR", nome="Paraná", perfil_padrao=PC.FRIO))
    sessao.add(Municipio(codigo_ibge=4106902, nome="Curitiba", nome_busca="curitiba", uf="PR"))
    sessao.flush()
    enxoval = _criar(sessao)

    with caplog.at_level(logging.WARNING):
        completo = ler_enxoval(sessao, enxoval.id, HOJE)

    assert completo.calculado.linhas == ()
    assert completo.progresso.total_unidades == 0
    assert completo.progresso.percentual == 0
    # banco migrado mas sem seed não pode passar em silêncio: quem opera precisa
    # de um sinal de que o catálogo está vazio (Review Focus 5).
    assert any("catálogo" in r.message.lower() for r in caplog.records)
    assert str(enxoval.id) not in caplog.text


def test_avisos_do_motor_vao_para_o_log_e_nao_para_a_resposta(catalogo_no_banco, caplog):
    import logging

    from app.db.catalogo import JanelaTamanho
    from app.db.enums import Tamanho

    # tira a janela do P: o motor passa a avisar
    catalogo_no_banco.query(JanelaTamanho).filter(JanelaTamanho.tamanho == Tamanho.P).delete()
    catalogo_no_banco.flush()
    enxoval = _criar(catalogo_no_banco)

    with caplog.at_level(logging.WARNING):
        completo = ler_enxoval(catalogo_no_banco, enxoval.id, HOJE)

    assert completo.calculado.avisos  # o motor avisou
    assert any("janela" in r.message for r in caplog.records)
    assert str(enxoval.id) not in caplog.text  # o id nunca vai para o log
