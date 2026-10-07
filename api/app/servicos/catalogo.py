"""Converte as tabelas do catálogo nas dataclasses do motor.

Esta é a única direção permitida: o motor nunca vê SQLAlchemy diretamente.
Este módulo funciona como **Anti-Corruption Layer** (ACL) do catálogo —
depois que os dados passam por aqui, o motor recebe apenas dataclasses
imutáveis (``@dataclass(frozen=True)``), sem referências ao ORM.

**Cache de catálogo:**
O catálogo (itens, fases, janelas, regras) raramente muda em produção — só
quando um administrador edita o conteúdo via ``/admin``. Para evitar 5 queries
a cada requisição, mantemos um cache em memória por processo invalidável via
``invalidar_cache_catalogo()``. A invalidação deve ser chamada por qualquer
operação que modifique o catálogo no banco (ex.: webhook, endpoint admin).

Funções públicas:
- ``carregar_catalogo``: carrega do banco ou retorna do cache.
- ``perfis_por_codigo``: retorna dicionário de perfis de clima (sem cache —
  raramente acessado e pequeno).
- ``invalidar_cache_catalogo``: limpa o cache forçando recarga na próxima leitura.
"""
import threading

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload, selectinload

from app.db import catalogo as tabelas
from app.db.enums import PerfilCodigo
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
    TamanhoDoItem,
)

# ---------------------------------------------------------------------------
# Cache de processo
# ---------------------------------------------------------------------------
# O catálogo é imutável em runtime normal. Guardamos uma única cópia por
# processo (thread-safe via Lock). Em testes, cada teste usa rollback de
# transação, então o cache entre testes pode vazar — ver nota abaixo.
# Nota: os testes que alteram o catálogo devem chamar invalidar_cache_catalogo()
# ou usar sessões diferentes para não ver dados obsoletos.

_cache_lock = threading.Lock()
_catalogo_cache: Catalogo | None = None


def invalidar_cache_catalogo() -> None:
    """Invalida o cache em memória do catálogo.

    Deve ser chamada após qualquer operação que modifique itens, fases,
    janelas ou regras de segurança no banco (ex.: endpoint de admin,
    hooks de CI/CD, testes que modificam o catálogo).
    """
    global _catalogo_cache
    with _cache_lock:
        _catalogo_cache = None


# ---------------------------------------------------------------------------
# Funções públicas
# ---------------------------------------------------------------------------


def perfis_por_codigo(sessao: Session) -> dict[PerfilCodigo, PerfilClima]:
    """Retorna todos os perfis de clima indexados pelo código.

    Não usa cache — perfis são poucos e raramente consultados fora do
    ciclo de leitura completa do enxoval.

    Args:
        sessao: Sessão SQLAlchemy ativa.

    Returns:
        Dicionário ``{PerfilCodigo: PerfilClima}``.
    """
    return {
        p.codigo: PerfilClima(
            codigo=p.codigo,
            meses_frios=frozenset(p.meses_frios or ()),
            meses_frescos=frozenset(p.meses_frescos or ()),
        )
        for p in sessao.scalars(select(tabelas.PerfilClima))
    }


def carregar_catalogo(sessao: Session) -> Catalogo:
    """Carrega o catálogo completo do banco ou retorna a versão em cache.

    Na primeira chamada (ou após ``invalidar_cache_catalogo()``), executa
    as queries necessárias com eager loading para evitar N+1 e armazena
    o resultado em cache de processo.

    Args:
        sessao: Sessão SQLAlchemy ativa (usada apenas se o cache estiver vazio).

    Returns:
        ``Catalogo`` imutável com itens, fases, janelas e regras de segurança.
    """
    global _catalogo_cache
    with _cache_lock:
        if _catalogo_cache is not None:
            return _catalogo_cache
        _catalogo_cache = _carregar_do_banco(sessao)
        return _catalogo_cache


# ---------------------------------------------------------------------------
# Funções internas
# ---------------------------------------------------------------------------


def _carregar_do_banco(sessao: Session) -> Catalogo:
    """Executa as queries e monta o Catalogo a partir dos dados do banco."""
    categorias = sessao.scalars(
        select(tabelas.Categoria).order_by(tabelas.Categoria.ordem)
    ).all()
    ordem_categoria = {c.id: c.ordem for c in categorias}

    itens = sessao.scalars(
        select(tabelas.Item).options(
            selectinload(tabelas.Item.tamanhos).selectinload(tabelas.ItemTamanho.fase_compra),
            selectinload(tabelas.Item.regras),
            selectinload(tabelas.Item.marcas).selectinload(tabelas.ItemMarca.marca),
            selectinload(tabelas.Item.regras_seguranca),
            joinedload(tabelas.Item.categoria),
            joinedload(tabelas.Item.fase_compra),
        )
    ).all()
    itens = sorted(itens, key=lambda i: (ordem_categoria.get(i.categoria_id, 10**6), i.ordem))

    return Catalogo(
        categorias=tuple(CategoriaCatalogo(c.slug, c.nome, c.ordem) for c in categorias),
        fases=tuple(
            Fase(f.codigo, f.nome, f.referencia, f.inicio, f.fim, f.texto, f.ordem)
            for f in sessao.scalars(
                select(tabelas.FaseRoteiro).order_by(tabelas.FaseRoteiro.ordem)
            )
        ),
        janelas=tuple(
            JanelaTamanho(j.tamanho, j.idade_inicio_dias, j.idade_fim_dias, j.peso_referencia)
            for j in sessao.scalars(select(tabelas.JanelaTamanho))
        ),
        itens=tuple(_converter_item(i) for i in itens),
        regras_seguranca=tuple(
            RegraSegurancaCatalogo(
                codigo=r.codigo,
                tema=r.tema,
                idade_inicio_meses=r.idade_inicio_meses,
                idade_fim_meses=r.idade_fim_meses,
                texto=r.texto,
                base=r.base,
                itens=tuple(i.slug for i in r.itens),
            )
            for r in sessao.scalars(
                select(tabelas.RegraSeguranca)
                .options(selectinload(tabelas.RegraSeguranca.itens))
                .order_by(tabelas.RegraSeguranca.id)
            )
        ),
    )


def _converter_item(item: tabelas.Item) -> ItemCatalogo:
    """Converte um modelo ORM ``Item`` na dataclass ``ItemCatalogo`` do motor.

    Args:
        item: Instância ORM com todos os relacionamentos já carregados
            (eager loading feito em ``_carregar_do_banco``).

    Returns:
        ``ItemCatalogo`` imutável.
    """
    return ItemCatalogo(
        slug=item.slug,
        nome=item.nome,
        categoria_slug=item.categoria.slug,
        fase_codigo=item.fase_compra.codigo,
        ordem=item.ordem,
        para_que_serve=item.para_que_serve,
        como_escolher=item.como_escolher,
        prioridade_base=item.prioridade_base,
        idade_inicio_meses=item.idade_inicio_meses,
        e_seguranca=item.e_seguranca,
        uso_clima=item.uso_clima,
        variante_frio=item.variante_frio,
        variante_calor=item.variante_calor,
        escala_lavagem=item.escala_lavagem,
        quantidade=item.quantidade,
        unidade_texto=item.unidade_texto,
        tamanhos=tuple(
            TamanhoDoItem(
                tamanho=t.tamanho,
                quantidade_base=t.quantidade_base,
                fase_codigo=t.fase_compra.codigo if t.fase_compra else None,
            )
            for t in item.tamanhos
        ),
        regras=tuple(RegraItem(r.condicao, r.efeito, r.valor) for r in item.regras),
        marcas=tuple(MarcaDoItem(v.marca.nome, v.faixa, v.ordem) for v in item.marcas),
        regras_seguranca=tuple(r.codigo for r in item.regras_seguranca),
    )
