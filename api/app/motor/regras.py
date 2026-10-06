from collections.abc import Iterable
from dataclasses import dataclass

from app.db.enums import Condicao, Efeito, Faixa, Moradia, PerfilCodigo, Prioridade
from app.motor.tipos import ItemCatalogo, MarcaDoItem, MarcasEscolhidas, Respostas

ORDEM_FAIXAS = (Faixa.ECONOMICO, Faixa.INTERMEDIARIO, Faixa.INVESTIR)


@dataclass(frozen=True)
class Avaliacao:
    incluir: bool
    prioridade: Prioridade
    dicas: tuple[str, ...]
    avisos: tuple[str, ...] = ()  # defeitos do catálogo encontrados nas regras deste item


def condicao_vale(condicao: Condicao, respostas: Respostas) -> bool:
    """Condições físicas da família: carro, moradia e clima. Orçamento e 'primeiro filho'
    não existem aqui de propósito: nenhuma regra pode tirar um item por preferência."""
    match condicao:
        case Condicao.COM_CARRO:
            return respostas.tem_carro
        case Condicao.SEM_CARRO:
            return not respostas.tem_carro
        case Condicao.APARTAMENTO:
            return respostas.moradia == Moradia.APARTAMENTO
        case Condicao.CASA_SEM_ESCADA:
            return respostas.moradia == Moradia.CASA_SEM_ESCADA
        case Condicao.CASA_COM_ESCADA:
            return respostas.moradia == Moradia.CASA_COM_ESCADA
        case Condicao.PERFIL_QUENTE:
            return respostas.perfil.codigo == PerfilCodigo.QUENTE
        case Condicao.PERFIL_MODERADO:
            return respostas.perfil.codigo == PerfilCodigo.MODERADO
        case Condicao.PERFIL_FRIO:
            return respostas.perfil.codigo == PerfilCodigo.FRIO


def avaliar_regras(item: ItemCatalogo, respostas: Respostas) -> Avaliacao:
    restricoes = [r for r in item.regras if r.efeito == Efeito.INCLUIR_SO_SE]
    incluir = not restricoes or any(condicao_vale(r.condicao, respostas) for r in restricoes)

    prioridade = item.prioridade_base
    dicas: list[str] = []
    avisos: list[str] = []
    validas = {p.value for p in Prioridade}
    for regra in item.regras:
        if not condicao_vale(regra.condicao, respostas):
            continue
        if regra.efeito == Efeito.MUDAR_PRIORIDADE:
            if regra.valor in validas:
                prioridade = Prioridade(regra.valor)
            else:
                avisos.append(
                    f"item '{item.slug}': regra de prioridade com valor inválido "
                    f"('{regra.valor}'); mantida a prioridade '{prioridade.value}'"
                )
        elif regra.efeito == Efeito.DICA and regra.valor:
            dicas.append(regra.valor)
    return Avaliacao(
        incluir=incluir, prioridade=prioridade, dicas=tuple(dicas), avisos=tuple(avisos)
    )


def marcas_para(marcas: Iterable[MarcaDoItem], orcamento: Faixa) -> MarcasEscolhidas:
    """Marcas da faixa do orçamento; se não houver, a faixa mais próxima (empate: a mais barata)."""
    marcas = sorted(marcas, key=lambda m: m.ordem)
    alvo = ORDEM_FAIXAS.index(orcamento)
    por_proximidade = sorted(
        ORDEM_FAIXAS, key=lambda f: (abs(ORDEM_FAIXAS.index(f) - alvo), ORDEM_FAIXAS.index(f))
    )
    for faixa in por_proximidade:
        nomes = tuple(m.nome for m in marcas if m.faixa == faixa)
        if nomes:
            return MarcasEscolhidas(nomes=nomes, faixa=faixa, fallback=faixa != orcamento)
    return MarcasEscolhidas(nomes=(), faixa=None, fallback=False)
