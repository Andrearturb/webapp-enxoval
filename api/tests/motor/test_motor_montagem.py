from dataclasses import replace
from datetime import date

import pytest

from app.db.enums import Faixa, Moradia, Prioridade, ReferenciaFase, Tamanho, UsoClima
from app.motor.montagem import montar_enxoval
from app.motor.tipos import Catalogo, CategoriaCatalogo, Fase, ItemCatalogo, JanelaTamanho, TamanhoDoItem

HOJE = date(2027, 2, 1)


def _linhas(enxoval) -> dict:
    return {linha.chave: linha for linha in enxoval.linhas}


def test_curitiba_com_nascimento_em_junho(catalogo, fazer_respostas):
    enxoval = montar_enxoval(fazer_respostas("frio"), catalogo, HOJE)
    linhas = _linhas(enxoval)

    # P cobre 15/jun a 12/set: tudo frio, então só a variante de frio
    assert linhas["body:P:frio"].quantidade == 8
    assert linhas["body:P:frio"].rotulo_variante == "manga longa"
    assert "body:P:calor" not in linhas
    # M cobre 13/set a 11/dez: 18 dias de frio em 90 (1/5), então 1 de frio e 6 de calor
    assert linhas["body:M:frio"].quantidade == 1
    assert linhas["body:M:calor"].quantidade == 6
    assert linhas["body:M:calor"].rotulo_variante == "manga curta"
    # peças só de frio aparecem nas janelas com mês frio (G cobre dez a mar, sem frio)
    gorros = {l.tamanho for l in enxoval.linhas if l.item_slug == "gorro"}
    assert gorros == {Tamanho.RN, Tamanho.P, Tamanho.M, Tamanho.GG}
    assert "saco-dormir::" in linhas
    assert "mosquiteiro::" not in linhas


def test_salvador_com_nascimento_em_junho(catalogo, fazer_respostas):
    enxoval = montar_enxoval(fazer_respostas("quente"), catalogo, HOJE)
    linhas = _linhas(enxoval)

    # P: 47 dias frescos (meio valor) em 90 = 47/180; 8 * 47/180 arredonda para 2
    assert linhas["body:P:frio"].quantidade == 2
    assert linhas["body:P:calor"].quantidade == 6
    # G cobre dez a mar: sem mês fresco, só calor
    assert linhas["body:G:calor"].quantidade == 6
    assert "body:G:frio" not in linhas
    # gorro e saco de dormir só entram com mês frio de verdade; mosquiteiro entra no calor
    assert not [l for l in enxoval.linhas if l.item_slug in ("gorro", "saco-dormir")]
    assert "mosquiteiro::" in linhas


def test_quantidade_acompanha_a_frequencia_de_lavagem(catalogo, fazer_respostas):
    a_cada_2 = _linhas(montar_enxoval(fazer_respostas("frio", dias=2), catalogo, HOJE))
    a_cada_3 = _linhas(montar_enxoval(fazer_respostas("frio", dias=3), catalogo, HOJE))

    assert a_cada_2["body:P:frio"].quantidade == 8
    assert a_cada_3["body:P:frio"].quantidade == 11
    # gorro não escala com a lavagem
    assert a_cada_3["gorro:P:"].quantidade == a_cada_2["gorro:P:"].quantidade == 2
    # item sem tamanho que escala: 4 lençóis viram ceil(4 * 4/3) = 6
    assert a_cada_3["lencol-elastico::"].quantidade == 6


def test_bebe_conforto_sem_carro_continua_na_lista_como_util(catalogo, fazer_respostas):
    com_carro = montar_enxoval(fazer_respostas(carro=True), catalogo, HOJE)
    sem_carro = montar_enxoval(fazer_respostas(carro=False), catalogo, HOJE)

    assert _linhas(com_carro)["bebe-conforto::"].prioridade == Prioridade.ESSENCIAL
    assert _linhas(sem_carro)["bebe-conforto::"].prioridade == Prioridade.UTIL
    ficha = next(f for f in sem_carro.fichas if f.slug == "bebe-conforto")
    assert any("táxi" in dica for dica in ficha.dicas)
    assert _linhas(sem_carro)["sling::"].prioridade == Prioridade.ESSENCIAL


@pytest.mark.parametrize(
    ("moradia", "tem_portao"),
    [(Moradia.APARTAMENTO, False), (Moradia.CASA_SEM_ESCADA, False), (Moradia.CASA_COM_ESCADA, True)],
)
def test_portao_so_em_casa_com_escada(catalogo, fazer_respostas, moradia, tem_portao):
    enxoval = montar_enxoval(fazer_respostas(moradia=moradia), catalogo, HOJE)

    assert ("portao-seguranca::" in _linhas(enxoval)) is tem_portao


def test_fase_de_compra_do_tamanho_prevalece_sobre_a_do_item(catalogo, fazer_respostas):
    linhas = _linhas(montar_enxoval(fazer_respostas("frio"), catalogo, HOJE))

    assert linhas["body:P:frio"].fase_codigo == "gestacao_7_8m"
    assert linhas["body:M:frio"].fase_codigo == "bebe_0_3m"
    assert linhas["body:GG:calor"].fase_codigo == "bebe_6_9m"
    assert linhas["berco::"].fase_codigo == "gestacao_5_7m"


def test_linhas_vem_na_ordem_das_categorias(catalogo, fazer_respostas):
    enxoval = montar_enxoval(fazer_respostas(), catalogo, HOJE)

    ordem_categoria = {c.slug: c.ordem for c in catalogo.categorias}
    ordens = [ordem_categoria[l.categoria_slug] for l in enxoval.linhas]
    assert ordens == sorted(ordens)
    assert enxoval.linhas[0].categoria_slug == "roupas"


def test_ficha_traz_as_marcas_da_faixa_do_orcamento(catalogo, fazer_respostas):
    intermediario = montar_enxoval(fazer_respostas(orcamento=Faixa.INTERMEDIARIO), catalogo, HOJE)
    economico = montar_enxoval(fazer_respostas(orcamento=Faixa.ECONOMICO), catalogo, HOJE)

    ficha = next(f for f in intermediario.fichas if f.slug == "berco")
    assert ficha.marcas.nomes == ("Tcil", "Reller")
    assert ficha.marcas.fallback is False
    ficha_economica = next(f for f in economico.fichas if f.slug == "berco")
    assert ficha_economica.marcas.nomes == ("Burigotto", "Galzerano")
    assert ficha_economica.regras_seguranca == ("inmetro-cordoes", "sono-seguro")


def test_roteiro_e_alertas_vem_junto(catalogo, fazer_respostas):
    enxoval = montar_enxoval(fazer_respostas(), catalogo, HOJE)

    assert len(enxoval.roteiro) == 8
    assert [f.codigo for f in enxoval.roteiro if f.atual] == ["gestacao_5_7m"]
    assert len(enxoval.alertas) == 8


def test_resumo_avisa_quando_o_volume_fica_alto_demais(catalogo, fazer_respostas):
    a_cada_2 = montar_enxoval(fazer_respostas("frio", dias=2), catalogo, HOJE)
    a_cada_4 = montar_enxoval(fazer_respostas("frio", dias=4), catalogo, HOJE)

    assert a_cada_2.resumo.dias_sem_lavar == 2
    assert a_cada_2.resumo.aviso_volume_alto is False
    assert a_cada_4.resumo.dias_sem_lavar == 4
    assert a_cada_4.resumo.aviso_volume_alto is True
    assert a_cada_4.resumo.total_unidades > a_cada_2.resumo.total_unidades


def test_limite_de_volume_e_configuravel(catalogo, fazer_respostas):
    enxoval = montar_enxoval(fazer_respostas("frio", dias=2), catalogo, HOJE, limite_volume=10)

    assert enxoval.resumo.aviso_volume_alto is True


def test_nao_ser_o_primeiro_filho_destaca_ja_tinha(catalogo, fazer_respostas):
    primeiro = montar_enxoval(fazer_respostas(primeiro_filho=True), catalogo, HOJE)
    segundo = montar_enxoval(fazer_respostas(primeiro_filho=False), catalogo, HOJE)

    assert primeiro.resumo.destacar_ja_tinha is False
    assert segundo.resumo.destacar_ja_tinha is True


def test_dias_entre_lavagens_invalido_e_recusado(catalogo, fazer_respostas):
    with pytest.raises(ValueError, match="entre 1 e 7"):
        montar_enxoval(fazer_respostas(dias=0), catalogo, HOJE)


# ---------- catálogo incompleto: o motor não quebra e avisa ----------

ITEM = ItemCatalogo(
    slug="body", nome="Body", categoria_slug="roupas", fase_codigo="f", ordem=1,
    para_que_serve="a", como_escolher="b", prioridade_base=Prioridade.ESSENCIAL,
    uso_clima=UsoClima.DIVIDE, variante_frio="longa", variante_calor="curta",
    escala_lavagem=True, tamanhos=(TamanhoDoItem(Tamanho.P, 8),),
)
CATEGORIAS = (CategoriaCatalogo("roupas", "Roupas", 1),)


def test_catalogo_vazio_devolve_enxoval_vazio(fazer_respostas):
    enxoval = montar_enxoval(fazer_respostas(), Catalogo(), HOJE)

    assert enxoval.linhas == () and enxoval.fichas == () and enxoval.roteiro == ()
    assert enxoval.resumo.total_unidades == 0
    assert enxoval.resumo.aviso_volume_alto is False


def test_item_sem_janela_do_tamanho_entra_sem_divisao_de_clima_e_avisa(fazer_respostas):
    catalogo = Catalogo(categorias=CATEGORIAS, itens=(ITEM,))

    enxoval = montar_enxoval(fazer_respostas("frio"), catalogo, HOJE)

    assert [(l.chave, l.quantidade) for l in enxoval.linhas] == [("body:P:", 8)]
    assert any("body" in aviso and "janela" in aviso for aviso in enxoval.avisos)


def test_item_sem_tamanhos_nem_quantidade_e_ignorado_com_aviso(fazer_respostas):
    vazio = replace(ITEM, tamanhos=())
    catalogo = Catalogo(categorias=CATEGORIAS, itens=(vazio,))

    enxoval = montar_enxoval(fazer_respostas(), catalogo, HOJE)

    assert enxoval.linhas == ()
    assert any("body" in aviso and "quantidade" in aviso for aviso in enxoval.avisos)


def test_item_sem_marcas_gera_ficha_sem_marcas(fazer_respostas):
    janela = JanelaTamanho(Tamanho.P, 0, 90)
    catalogo = Catalogo(categorias=CATEGORIAS, itens=(ITEM,), janelas=(janela,))

    enxoval = montar_enxoval(fazer_respostas("frio"), catalogo, HOJE)

    assert enxoval.fichas[0].marcas.nomes == ()
    assert enxoval.fichas[0].marcas.faixa is None


def test_fase_de_roteiro_sem_itens_nao_atrapalha(fazer_respostas):
    fase = Fase("f", "Fase", ReferenciaFase.BEBE_MES, 0, 2, "t", 1)

    enxoval = montar_enxoval(fazer_respostas(), Catalogo(fases=(fase,)), HOJE)

    assert len(enxoval.roteiro) == 1


def test_janela_de_tamanho_degenerada_avisa_em_vez_de_quebrar(fazer_respostas):
    """Um erro de digitação no admin (início = fim) não pode derrubar o enxoval de todos."""
    janela_torta = JanelaTamanho(Tamanho.P, 90, 90)
    catalogo = Catalogo(categorias=CATEGORIAS, itens=(ITEM,), janelas=(janela_torta,))

    enxoval = montar_enxoval(fazer_respostas("frio"), catalogo, HOJE)

    assert [(l.chave, l.quantidade) for l in enxoval.linhas] == [("body:P:", 8)]
    assert any("body" in a and "inválida" in a for a in enxoval.avisos)


def test_regra_de_prioridade_sem_valor_avisa_em_vez_de_quebrar(fazer_respostas):
    from app.db.enums import Condicao, Efeito
    from app.motor.tipos import RegraItem

    sem_valor = replace(
        ITEM,
        tamanhos=(),
        quantidade=1,
        uso_clima=UsoClima.NEUTRO,
        regras=(RegraItem(Condicao.APARTAMENTO, Efeito.MUDAR_PRIORIDADE, None),),
    )
    catalogo = Catalogo(categorias=CATEGORIAS, itens=(sem_valor,))

    enxoval = montar_enxoval(fazer_respostas(moradia=Moradia.APARTAMENTO), catalogo, HOJE)

    assert enxoval.linhas[0].prioridade == Prioridade.ESSENCIAL  # mantém a base
    assert any("body" in a and "prioridade" in a for a in enxoval.avisos)


def test_avisos_trazem_so_defeitos_de_catalogo_nao_fallback_de_marca(catalogo, fazer_respostas):
    """O fallback de faixa é normal e já viaja em ficha.marcas; avisos é canal de defeito."""
    enxoval = montar_enxoval(fazer_respostas(orcamento=Faixa.INTERMEDIARIO), catalogo, HOJE)

    assert enxoval.avisos == ()
    manta = next(f for f in enxoval.fichas if f.slug == "manta")
    assert manta.marcas.fallback is True
    assert manta.marcas.faixa == Faixa.ECONOMICO


def test_alerta_so_aponta_para_itens_que_estao_no_enxoval(catalogo, fazer_respostas):
    """Apartamento não tem portão: o alerta da casa não pode linkar para ele."""
    apartamento = montar_enxoval(fazer_respostas(moradia=Moradia.APARTAMENTO), catalogo, HOJE)
    com_escada = montar_enxoval(fazer_respostas(moradia=Moradia.CASA_COM_ESCADA), catalogo, HOJE)

    presentes = {f.slug for f in apartamento.fichas}
    for alerta in apartamento.alertas:
        assert set(alerta.itens) <= presentes, alerta.codigo
    casa = next(a for a in apartamento.alertas if a.codigo == "casa-antes-de-engatinhar")
    assert "portao-seguranca" not in casa.itens
    casa_escada = next(a for a in com_escada.alertas if a.codigo == "casa-antes-de-engatinhar")
    assert "portao-seguranca" in casa_escada.itens
