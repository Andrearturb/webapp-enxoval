from datetime import date
from itertools import product

from app.db.enums import Faixa, Moradia
from app.motor.montagem import montar_enxoval

HOJE = date(2027, 2, 1)
PERFIS = ("quente", "moderado", "frio")
DIAS = (1, 2, 4, 7)


def test_item_de_seguranca_nunca_sai_por_orcamento_ou_preferencia(catalogo, fazer_respostas):
    de_seguranca = {i.slug for i in catalogo.itens if i.e_seguranca}
    assert len(de_seguranca) == 9  # berço, colchão, lençol, bebê conforto, termômetro, 4 da casa

    for perfil, moradia, carro, orcamento, primeiro_filho, dias in product(
        PERFIS, Moradia, (True, False), Faixa, (True, False), DIAS
    ):
        respostas = fazer_respostas(
            perfil, dias=dias, moradia=moradia, carro=carro,
            orcamento=orcamento, primeiro_filho=primeiro_filho,
        )
        enxoval = montar_enxoval(respostas, catalogo, HOJE)

        presentes = {l.item_slug for l in enxoval.linhas if l.e_seguranca}
        # só uma condição física tira um item de segurança: o portão sem escada
        esperados = de_seguranca - (
            set() if moradia == Moradia.CASA_COM_ESCADA else {"portao-seguranca"}
        )
        assert presentes == esperados, (perfil, moradia, carro, orcamento, primeiro_filho, dias)
        assert len(enxoval.alertas) == 8


def test_orcamento_e_primeiro_filho_so_mudam_marcas_e_destaque_nunca_as_linhas(
    catalogo, fazer_respostas
):
    for perfil, moradia, carro, dias in product(PERFIS, Moradia, (True, False), DIAS):
        referencia = montar_enxoval(
            fazer_respostas(perfil, dias=dias, moradia=moradia, carro=carro), catalogo, HOJE
        )
        for orcamento, primeiro_filho in product(Faixa, (True, False)):
            outra = montar_enxoval(
                fazer_respostas(
                    perfil, dias=dias, moradia=moradia, carro=carro,
                    orcamento=orcamento, primeiro_filho=primeiro_filho,
                ),
                catalogo,
                HOJE,
            )
            assert outra.linhas == referencia.linhas, (perfil, moradia, carro, dias, orcamento)
            assert outra.alertas == referencia.alertas
            # o texto de segurança e as dicas do cartão também não podem mudar por orçamento
            def _invariante(fichas):
                return [(f.slug, f.regras_seguranca, f.dicas, f.idade_inicio_meses) for f in fichas]

            assert _invariante(outra.fichas) == _invariante(referencia.fichas)
