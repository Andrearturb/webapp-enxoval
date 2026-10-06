from datetime import date

import pytest

from app.db.enums import (
    Condicao,
    Efeito,
    Faixa,
    Moradia,
    PerfilCodigo,
    Prioridade,
    ReferenciaFase,
    Tamanho,
    TemaSeguranca,
    UsoClima,
)
from app.motor.tipos import (
    Catalogo,
    CategoriaCatalogo,
    Fase,
    ItemCatalogo,
    JanelaTamanho,
    MarcaDoItem,
    PerfilClima,
    RegraItem,
    RegraSegurancaCatalogo,
    Respostas,
    TamanhoDoItem,
)
from seed.util import ler_yaml


@pytest.fixture(scope="session")
def perfis() -> dict[str, PerfilClima]:
    return {
        p["codigo"]: PerfilClima(
            PerfilCodigo(p["codigo"]),
            frozenset(p["meses_frios"]),
            frozenset(p["meses_frescos"]),
        )
        for p in ler_yaml("perfis.yaml")
    }


@pytest.fixture(scope="session")
def catalogo() -> Catalogo:
    faixas = {m["nome"]: Faixa(m["faixa"]) for m in ler_yaml("marcas.yaml")}
    seguranca = ler_yaml("seguranca.yaml")
    codigos_por_item: dict[str, list[str]] = {}
    for regra in seguranca:
        for slug in regra.get("itens", []):
            codigos_por_item.setdefault(slug, []).append(regra["codigo"])

    itens = []
    for ordem, bruto in enumerate(ler_yaml("itens.yaml")["itens"], start=1):
        fases_tamanho = bruto.get("fases_tamanho", {})
        variantes = bruto.get("variantes", {})
        marcas = []
        for posicao, entrada in enumerate(bruto.get("marcas", []), start=1):
            nome, faixa = (
                (entrada, None) if isinstance(entrada, str) else (entrada["nome"], entrada.get("faixa"))
            )
            marcas.append(MarcaDoItem(nome, Faixa(faixa) if faixa else faixas[nome], posicao))
        itens.append(
            ItemCatalogo(
                slug=bruto["slug"],
                nome=bruto["nome"],
                categoria_slug=bruto["categoria"],
                fase_codigo=bruto["fase"],
                ordem=ordem,
                para_que_serve=bruto["para_que_serve"],
                como_escolher=bruto["como_escolher"],
                prioridade_base=Prioridade(bruto["prioridade"]),
                idade_inicio_meses=bruto.get("idade_inicio_meses", 0),
                e_seguranca=bruto.get("seguranca", False),
                uso_clima=UsoClima(bruto.get("uso_clima", "neutro")),
                variante_frio=variantes.get("frio"),
                variante_calor=variantes.get("calor"),
                escala_lavagem=bruto.get("escala_lavagem", False),
                quantidade=bruto.get("quantidade"),
                unidade_texto=bruto.get("unidade"),
                tamanhos=tuple(
                    TamanhoDoItem(Tamanho(t), q, fases_tamanho.get(t))
                    for t, q in bruto.get("tamanhos", {}).items()
                ),
                regras=tuple(
                    RegraItem(Condicao(r["condicao"]), Efeito(r["efeito"]), r.get("valor"))
                    for r in bruto.get("regras", [])
                ),
                marcas=tuple(marcas),
                regras_seguranca=tuple(codigos_por_item.get(bruto["slug"], [])),
            )
        )

    return Catalogo(
        categorias=tuple(
            CategoriaCatalogo(c["slug"], c["nome"], c["ordem"]) for c in ler_yaml("categorias.yaml")
        ),
        fases=tuple(
            Fase(
                f["codigo"], f["nome"], ReferenciaFase(f["referencia"]),
                f["inicio"], f["fim"], f["texto"], f["ordem"],
            )
            for f in ler_yaml("fases.yaml")
        ),
        janelas=tuple(
            JanelaTamanho(
                Tamanho(j["tamanho"]), j["idade_inicio_dias"], j["idade_fim_dias"],
                j["peso_referencia"],
            )
            for j in ler_yaml("janelas.yaml")
        ),
        itens=tuple(itens),
        regras_seguranca=tuple(
            RegraSegurancaCatalogo(
                r["codigo"], TemaSeguranca(r["tema"]), r["idade_inicio_meses"],
                r["idade_fim_meses"], r["texto"], r["base"], tuple(r.get("itens", [])),
            )
            for r in seguranca
        ),
    )


@pytest.fixture
def fazer_respostas(perfis):
    def _fazer(
        perfil="frio",
        data_prevista=date(2027, 6, 15),
        dias=2,
        moradia=Moradia.APARTAMENTO,
        carro=True,
        orcamento=Faixa.INTERMEDIARIO,
        primeiro_filho=True,
    ) -> Respostas:
        return Respostas(
            perfil=perfis[perfil],
            data_prevista=data_prevista,
            dias_entre_lavagens=dias,
            moradia=moradia,
            tem_carro=carro,
            orcamento=orcamento,
            primeiro_filho=primeiro_filho,
        )

    return _fazer
