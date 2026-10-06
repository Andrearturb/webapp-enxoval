import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, coluna_enum
from app.db.enums import Faixa, Moradia, PerfilCodigo


class Enxoval(Base):
    """Respostas do questionário de uma família. A lista é recalculada na leitura."""

    __tablename__ = "enxoval"
    __table_args__ = (
        CheckConstraint(
            "dias_entre_lavagens BETWEEN 1 AND 7", name="dias_entre_lavagens_valido"
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    municipio_codigo: Mapped[int] = mapped_column(ForeignKey("municipio.codigo_ibge"))
    perfil_clima: Mapped[PerfilCodigo] = mapped_column(coluna_enum(PerfilCodigo))
    perfil_corrigido: Mapped[bool] = mapped_column(default=False)
    data_prevista: Mapped[date] = mapped_column(Date)
    dias_entre_lavagens: Mapped[int] = mapped_column(SmallInteger)
    moradia: Mapped[Moradia] = mapped_column(coluna_enum(Moradia))
    tem_carro: Mapped[bool]
    orcamento: Mapped[Faixa] = mapped_column(coluna_enum(Faixa))
    primeiro_filho: Mapped[bool]

    linhas: Mapped[list["EnxovalLinha"]] = relationship(
        back_populates="enxoval", cascade="all, delete-orphan", passive_deletes=True
    )


class EnxovalLinha(Base):
    """Quantidades marcadas numa linha. `chave` = '<slug>:<tamanho>:<variante>'."""

    __tablename__ = "enxoval_linha"
    __table_args__ = (
        CheckConstraint(
            "qtd_comprada >= 0 AND qtd_ganhada >= 0 AND qtd_ja_tinha >= 0",
            name="quantidades_nao_negativas",
        ),
    )

    enxoval_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("enxoval.id", ondelete="CASCADE"), primary_key=True
    )
    chave: Mapped[str] = mapped_column(String(140), primary_key=True)
    qtd_comprada: Mapped[int] = mapped_column(default=0)
    qtd_ganhada: Mapped[int] = mapped_column(default=0)
    qtd_ja_tinha: Mapped[int] = mapped_column(default=0)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    enxoval: Mapped[Enxoval] = relationship(back_populates="linhas")
