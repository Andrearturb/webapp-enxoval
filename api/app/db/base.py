from enum import StrEnum

from sqlalchemy import Enum, MetaData
from sqlalchemy.orm import DeclarativeBase

CONVENCAO_NOMES = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=CONVENCAO_NOMES)


def coluna_enum(enum_cls: type[StrEnum]) -> Enum:
    """Enum gravado como texto (o valor, ex.: 'essencial'), validado no Python."""
    return Enum(
        enum_cls,
        native_enum=False,
        create_constraint=False,
        length=30,
        validate_strings=True,
        values_callable=lambda membros: [m.value for m in membros],
    )
