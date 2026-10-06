from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.catalogo import (
    Categoria,
    FaseRoteiro,
    Item,
    ItemMarca,
    ItemRegra,
    ItemTamanho,
    Marca,
)
from app.db.enums import Condicao, Efeito, Faixa, Prioridade, Tamanho, UsoClima
from seed.util import buscar, enum_de, inserir_se_faltar, ler_yaml, validar_campos


CAMPOS_OBRIGATORIOS = {
    "slug", "nome", "categoria", "fase", "prioridade", "para_que_serve", "como_escolher",
}
CAMPOS_OPCIONAIS = {
    "seguranca", "uso_clima", "variantes", "escala_lavagem", "quantidade", "unidade",
    "idade_inicio_meses", "tamanhos", "fases_tamanho", "regras", "marcas",
}


def carregar_marcas(sessao: Session) -> int:
    linhas = [
        {"nome": m["nome"], "faixa_padrao": enum_de(Faixa, m["faixa"], f"marca '{m['nome']}'")}
        for m in ler_yaml("marcas.yaml")
    ]
    return inserir_se_faltar(sessao, Marca, linhas, ["nome"])


def carregar_itens(sessao: Session, dados: dict | None = None) -> dict[str, int]:
    """Cria os itens que ainda não existem. Item existente é ignorado (o admin manda)."""
    dados = dados if dados is not None else ler_yaml("itens.yaml")
    categorias = {c.slug: c.id for c in sessao.scalars(select(Categoria))}
    fases = {f.codigo: f.id for f in sessao.scalars(select(FaseRoteiro))}
    marcas = {m.nome: m for m in sessao.scalars(select(Marca))}
    existentes = set(sessao.scalars(select(Item.slug)))
    contagem = {"item": 0, "item_tamanho": 0, "item_regra": 0, "item_marca": 0}

    for ordem, bruto in enumerate(dados["itens"], start=1):
        ctx = f"item '{bruto.get('slug', '?')}'"
        validar_campos(bruto, CAMPOS_OBRIGATORIOS, CAMPOS_OPCIONAIS, ctx)
        slug = bruto["slug"]
        if slug in existentes:
            continue
        sem_quantidade = set(bruto.get("fases_tamanho", {})) - set(bruto.get("tamanhos", {}))
        if sem_quantidade:
            raise ValueError(
                f"{ctx}: fases_tamanho tem tamanho(s) sem quantidade em 'tamanhos': "
                f"{', '.join(sorted(sem_quantidade))}"
            )
        variantes = bruto.get("variantes", {})
        item = Item(
            slug=slug,
            nome=bruto["nome"],
            categoria_id=buscar(categorias, bruto["categoria"], ctx, "categoria"),
            fase_compra_id=buscar(fases, bruto["fase"], ctx, "fase"),
            prioridade_base=enum_de(Prioridade, bruto["prioridade"], ctx),
            e_seguranca=bruto.get("seguranca", False),
            uso_clima=enum_de(UsoClima, bruto.get("uso_clima", "neutro"), ctx),
            variante_frio=variantes.get("frio"),
            variante_calor=variantes.get("calor"),
            escala_lavagem=bruto.get("escala_lavagem", False),
            quantidade=bruto.get("quantidade"),
            unidade_texto=bruto.get("unidade"),
            idade_inicio_meses=bruto.get("idade_inicio_meses", 0),
            para_que_serve=bruto["para_que_serve"],
            como_escolher=bruto["como_escolher"],
            ordem=ordem,
        )

        fases_tamanho = bruto.get("fases_tamanho", {})
        for tamanho, quantidade in bruto.get("tamanhos", {}).items():
            fase = fases_tamanho.get(tamanho)
            item.tamanhos.append(
                ItemTamanho(
                    tamanho=enum_de(Tamanho, tamanho, ctx),
                    quantidade_base=quantidade,
                    fase_compra_id=buscar(fases, fase, ctx, "fase") if fase else None,
                )
            )
        if not item.tamanhos and item.quantidade is None:
            raise ValueError(f"{ctx}: informe 'tamanhos' ou 'quantidade'")

        for regra in bruto.get("regras", []):
            efeito = enum_de(Efeito, regra["efeito"], ctx)
            valor = regra.get("valor")
            if efeito == Efeito.MUDAR_PRIORIDADE:
                valor = enum_de(Prioridade, valor, ctx).value
            item.regras.append(
                ItemRegra(
                    condicao=enum_de(Condicao, regra["condicao"], ctx),
                    efeito=efeito,
                    valor=valor,
                )
            )

        for posicao, entrada in enumerate(bruto.get("marcas", []), start=1):
            nome, faixa = (
                (entrada, None) if isinstance(entrada, str)
                else (entrada["nome"], entrada.get("faixa"))
            )
            marca = buscar(marcas, nome, ctx, "marca")
            item.marcas.append(
                ItemMarca(
                    marca=marca,
                    faixa=enum_de(Faixa, faixa, ctx) if faixa else marca.faixa_padrao,
                    ordem=posicao,
                )
            )

        sessao.add(item)
        contagem["item"] += 1
        contagem["item_tamanho"] += len(item.tamanhos)
        contagem["item_regra"] += len(item.regras)
        contagem["item_marca"] += len(item.marcas)

    sessao.flush()
    return contagem
