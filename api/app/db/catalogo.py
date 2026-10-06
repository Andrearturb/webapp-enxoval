from datetime import date

from sqlalchemy import (
    JSON,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    String,
    Table,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, coluna_enum
from app.db.enums import (
    Condicao,
    Efeito,
    Faixa,
    PerfilCodigo,
    Prioridade,
    ReferenciaFase,
    Tamanho,
    TemaSeguranca,
    UsoClima,
)


class Categoria(Base):
    __tablename__ = "categoria"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(60), unique=True)
    nome: Mapped[str] = mapped_column(String(80))
    ordem: Mapped[int] = mapped_column(default=0)

    def __str__(self) -> str:
        return self.nome


class FaseRoteiro(Base):
    """Fase do roteiro de compras; início e fim na unidade de `referencia`."""

    __tablename__ = "fase_roteiro"
    __table_args__ = (CheckConstraint("fim >= inicio", name="intervalo_valido"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(40), unique=True)
    nome: Mapped[str] = mapped_column(String(80))
    referencia: Mapped[ReferenciaFase] = mapped_column(coluna_enum(ReferenciaFase))
    inicio: Mapped[int]
    fim: Mapped[int]
    texto: Mapped[str] = mapped_column(Text)
    ordem: Mapped[int] = mapped_column(default=0)

    def __str__(self) -> str:
        return self.nome


item_regra_seguranca = Table(
    "item_regra_seguranca",
    Base.metadata,
    Column("item_id", ForeignKey("item.id", ondelete="CASCADE"), primary_key=True),
    Column(
        "regra_seguranca_id",
        ForeignKey("regra_seguranca.id", ondelete="CASCADE"),
        primary_key=True,
    ),
)


class Item(Base):
    __tablename__ = "item"
    __table_args__ = (
        CheckConstraint(
            "quantidade IS NULL OR quantidade >= 1", name="quantidade_positiva"
        ),
        CheckConstraint(
            "uso_clima <> 'divide' OR "
            "(variante_frio IS NOT NULL AND variante_calor IS NOT NULL)",
            name="variantes_obrigatorias",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True)
    nome: Mapped[str] = mapped_column(String(120))
    categoria_id: Mapped[int] = mapped_column(ForeignKey("categoria.id"))
    fase_compra_id: Mapped[int] = mapped_column(ForeignKey("fase_roteiro.id"))
    para_que_serve: Mapped[str] = mapped_column(Text)
    como_escolher: Mapped[str] = mapped_column(Text)
    idade_inicio_meses: Mapped[int] = mapped_column(default=0)
    prioridade_base: Mapped[Prioridade] = mapped_column(coluna_enum(Prioridade))
    e_seguranca: Mapped[bool] = mapped_column(default=False)
    uso_clima: Mapped[UsoClima] = mapped_column(
        coluna_enum(UsoClima), default=UsoClima.NEUTRO
    )
    variante_frio: Mapped[str | None] = mapped_column(String(60))
    variante_calor: Mapped[str | None] = mapped_column(String(60))
    escala_lavagem: Mapped[bool] = mapped_column(default=False)
    quantidade: Mapped[int | None]
    unidade_texto: Mapped[str | None] = mapped_column(String(120))
    ordem: Mapped[int] = mapped_column(default=0)

    categoria: Mapped[Categoria] = relationship()
    fase_compra: Mapped[FaseRoteiro] = relationship()
    tamanhos: Mapped[list["ItemTamanho"]] = relationship(
        back_populates="item", cascade="all, delete-orphan", order_by="ItemTamanho.id"
    )
    regras: Mapped[list["ItemRegra"]] = relationship(
        back_populates="item", cascade="all, delete-orphan", order_by="ItemRegra.id"
    )
    marcas: Mapped[list["ItemMarca"]] = relationship(
        back_populates="item", cascade="all, delete-orphan", order_by="ItemMarca.ordem"
    )
    regras_seguranca: Mapped[list["RegraSeguranca"]] = relationship(
        secondary=item_regra_seguranca, back_populates="itens"
    )

    def __str__(self) -> str:
        return self.nome


class ItemTamanho(Base):
    __tablename__ = "item_tamanho"
    __table_args__ = (
        UniqueConstraint("item_id", "tamanho"),
        CheckConstraint("quantidade_base >= 0", name="quantidade_nao_negativa"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("item.id", ondelete="CASCADE"))
    tamanho: Mapped[Tamanho] = mapped_column(coluna_enum(Tamanho))
    quantidade_base: Mapped[int]
    # Fase de compra deste tamanho; vazio = usa a fase do item.
    fase_compra_id: Mapped[int | None] = mapped_column(ForeignKey("fase_roteiro.id"))

    item: Mapped[Item] = relationship(back_populates="tamanhos")
    fase_compra: Mapped[FaseRoteiro | None] = relationship()

    def __str__(self) -> str:
        return f"{self.item}: {self.tamanho} ({self.quantidade_base})"


class ItemRegra(Base):
    __tablename__ = "item_regra"
    __table_args__ = (UniqueConstraint("item_id", "condicao", "efeito"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("item.id", ondelete="CASCADE"))
    condicao: Mapped[Condicao] = mapped_column(coluna_enum(Condicao))
    efeito: Mapped[Efeito] = mapped_column(coluna_enum(Efeito))
    # mudar_prioridade: valor de Prioridade; dica: o texto; incluir_so_se: vazio.
    valor: Mapped[str | None] = mapped_column(String(500))

    item: Mapped[Item] = relationship(back_populates="regras")

    def __str__(self) -> str:
        return f"{self.item}: {self.condicao} → {self.efeito}"


class JanelaTamanho(Base):
    __tablename__ = "janela_tamanho"

    id: Mapped[int] = mapped_column(primary_key=True)
    tamanho: Mapped[Tamanho] = mapped_column(coluna_enum(Tamanho), unique=True)
    idade_inicio_dias: Mapped[int]
    idade_fim_dias: Mapped[int]
    peso_referencia: Mapped[str | None] = mapped_column(String(60))


class PerfilClima(Base):
    __tablename__ = "perfil_clima"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[PerfilCodigo] = mapped_column(coluna_enum(PerfilCodigo), unique=True)
    nome: Mapped[str] = mapped_column(String(60))
    descricao: Mapped[str] = mapped_column(Text)
    meses_frios: Mapped[list[int]] = mapped_column(JSON, default=list)
    meses_frescos: Mapped[list[int]] = mapped_column(JSON, default=list)

    def __str__(self) -> str:
        return self.nome


class Estado(Base):
    __tablename__ = "estado"

    uf: Mapped[str] = mapped_column(String(2), primary_key=True)
    nome: Mapped[str] = mapped_column(String(40))
    perfil_padrao: Mapped[PerfilCodigo] = mapped_column(coluna_enum(PerfilCodigo))

    def __str__(self) -> str:
        return self.nome


class Municipio(Base):
    __tablename__ = "municipio"

    codigo_ibge: Mapped[int] = mapped_column(primary_key=True, autoincrement=False)
    nome: Mapped[str] = mapped_column(String(80))
    nome_busca: Mapped[str] = mapped_column(String(80), index=True)
    uf: Mapped[str] = mapped_column(ForeignKey("estado.uf"))
    perfil_excecao: Mapped[PerfilCodigo | None] = mapped_column(
        coluna_enum(PerfilCodigo)
    )

    estado: Mapped[Estado] = relationship()

    def __str__(self) -> str:
        return f"{self.nome}/{self.uf}"


class Marca(Base):
    __tablename__ = "marca"

    id: Mapped[int] = mapped_column(primary_key=True)
    nome: Mapped[str] = mapped_column(String(80), unique=True)
    faixa_padrao: Mapped[Faixa] = mapped_column(coluna_enum(Faixa))
    validado: Mapped[bool] = mapped_column(default=False)
    fonte: Mapped[str | None] = mapped_column(Text)
    revisado_em: Mapped[date | None] = mapped_column(Date)

    vinculos: Mapped[list["ItemMarca"]] = relationship(
        back_populates="marca", cascade="all, delete-orphan", passive_deletes=True
    )

    def __str__(self) -> str:
        return self.nome


class ItemMarca(Base):
    __tablename__ = "item_marca"
    __table_args__ = (UniqueConstraint("item_id", "marca_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    item_id: Mapped[int] = mapped_column(ForeignKey("item.id", ondelete="CASCADE"))
    marca_id: Mapped[int] = mapped_column(ForeignKey("marca.id", ondelete="CASCADE"))
    faixa: Mapped[Faixa] = mapped_column(coluna_enum(Faixa))
    ordem: Mapped[int] = mapped_column(default=0)

    item: Mapped[Item] = relationship(back_populates="marcas")
    marca: Mapped[Marca] = relationship(back_populates="vinculos")

    def __str__(self) -> str:
        return f"{self.item} → {self.marca} ({self.faixa})"


class RegraSeguranca(Base):
    __tablename__ = "regra_seguranca"
    __table_args__ = (
        CheckConstraint(
            "idade_fim_meses >= idade_inicio_meses", name="intervalo_valido"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(60), unique=True)
    tema: Mapped[TemaSeguranca] = mapped_column(coluna_enum(TemaSeguranca))
    idade_inicio_meses: Mapped[int]
    idade_fim_meses: Mapped[int]
    texto: Mapped[str] = mapped_column(Text)
    base: Mapped[str] = mapped_column(String(120))
    validado: Mapped[bool] = mapped_column(default=False)
    fonte: Mapped[str | None] = mapped_column(Text)
    revisado_em: Mapped[date | None] = mapped_column(Date)

    itens: Mapped[list[Item]] = relationship(
        secondary=item_regra_seguranca, back_populates="regras_seguranca"
    )

    def __str__(self) -> str:
        return self.codigo
