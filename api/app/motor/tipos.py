"""Tipos do motor: dados simples de entrada e de saída, sem banco nem HTTP.

Os enums vêm de app.db.enums, que é um módulo de enums puros (sem SQLAlchemy).
"""
from dataclasses import dataclass
from datetime import date

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

# ---------- Entrada: catálogo ----------


@dataclass(frozen=True)
class PerfilClima:
    codigo: PerfilCodigo
    meses_frios: frozenset[int]
    meses_frescos: frozenset[int]


@dataclass(frozen=True)
class JanelaTamanho:
    tamanho: Tamanho
    inicio_dias: int
    fim_dias: int
    peso_referencia: str | None = None


@dataclass(frozen=True)
class Fase:
    codigo: str
    nome: str
    referencia: ReferenciaFase
    inicio: int
    fim: int
    texto: str
    ordem: int


@dataclass(frozen=True)
class RegraItem:
    condicao: Condicao
    efeito: Efeito
    valor: str | None = None


@dataclass(frozen=True)
class MarcaDoItem:
    nome: str
    faixa: Faixa
    ordem: int


@dataclass(frozen=True)
class TamanhoDoItem:
    tamanho: Tamanho
    quantidade_base: int
    fase_codigo: str | None = None


@dataclass(frozen=True)
class ItemCatalogo:
    slug: str
    nome: str
    categoria_slug: str
    fase_codigo: str
    ordem: int
    para_que_serve: str
    como_escolher: str
    prioridade_base: Prioridade
    idade_inicio_meses: int = 0
    e_seguranca: bool = False
    uso_clima: UsoClima = UsoClima.NEUTRO
    variante_frio: str | None = None
    variante_calor: str | None = None
    escala_lavagem: bool = False
    quantidade: int | None = None
    unidade_texto: str | None = None
    tamanhos: tuple[TamanhoDoItem, ...] = ()
    regras: tuple[RegraItem, ...] = ()
    marcas: tuple[MarcaDoItem, ...] = ()
    regras_seguranca: tuple[str, ...] = ()


@dataclass(frozen=True)
class CategoriaCatalogo:
    slug: str
    nome: str
    ordem: int


@dataclass(frozen=True)
class RegraSegurancaCatalogo:
    codigo: str
    tema: TemaSeguranca
    idade_inicio_meses: int
    idade_fim_meses: int
    texto: str
    base: str
    itens: tuple[str, ...] = ()


@dataclass(frozen=True)
class Catalogo:
    categorias: tuple[CategoriaCatalogo, ...] = ()
    fases: tuple[Fase, ...] = ()
    janelas: tuple[JanelaTamanho, ...] = ()
    itens: tuple[ItemCatalogo, ...] = ()
    regras_seguranca: tuple[RegraSegurancaCatalogo, ...] = ()


# ---------- Entrada: respostas da família ----------


@dataclass(frozen=True)
class Respostas:
    perfil: PerfilClima
    data_prevista: date
    dias_entre_lavagens: int
    moradia: Moradia
    tem_carro: bool
    orcamento: Faixa
    primeiro_filho: bool


# ---------- Saída ----------


@dataclass(frozen=True)
class LinhaCalculada:
    """Uma linha da planilha. `chave` = '<slug>:<tamanho>:<variante>' (ex.: 'body:P:frio')."""

    chave: str
    item_slug: str
    nome: str
    categoria_slug: str
    tamanho: Tamanho | None
    variante: str  # "", "frio" ou "calor"
    rotulo_variante: str | None  # ex.: "manga longa"
    quantidade: int
    unidade_texto: str | None
    prioridade: Prioridade
    fase_codigo: str
    e_seguranca: bool
    escala_lavagem: bool


@dataclass(frozen=True)
class MarcasEscolhidas:
    nomes: tuple[str, ...]
    faixa: Faixa | None
    fallback: bool  # True quando a faixa pedida não tinha marcas e usamos a vizinha


@dataclass(frozen=True)
class Ficha:
    slug: str
    nome: str
    para_que_serve: str
    como_escolher: str
    idade_inicio_meses: int
    marcas: MarcasEscolhidas
    dicas: tuple[str, ...]
    regras_seguranca: tuple[str, ...]


@dataclass(frozen=True)
class FaseCalculada:
    codigo: str
    nome: str
    texto: str
    inicio: date
    fim: date
    atual: bool


@dataclass(frozen=True)
class Alerta:
    codigo: str
    tema: TemaSeguranca
    texto: str
    base: str
    ativo_a_partir: date
    ativo_ate: date
    itens: tuple[str, ...]


@dataclass(frozen=True)
class Resumo:
    dias_sem_lavar: int
    total_unidades: int
    aviso_volume_alto: bool
    destacar_ja_tinha: bool


@dataclass(frozen=True)
class EnxovalCalculado:
    linhas: tuple[LinhaCalculada, ...]
    fichas: tuple[Ficha, ...]
    roteiro: tuple[FaseCalculada, ...]
    alertas: tuple[Alerta, ...]
    resumo: Resumo
    avisos: tuple[str, ...]
