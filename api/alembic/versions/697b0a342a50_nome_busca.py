"""nome_busca

Revision ID: 697b0a342a50
Revises: 78d8b021c91c
Create Date: 2026-10-06 12:24:49.597273

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '697b0a342a50'
down_revision: Union[str, Sequence[str], None] = '78d8b021c91c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Recalcula nome_busca com a regra nova (apóstrofo e hífen viram espaço)."""
    from app.texto import normalizar_busca

    conexao = op.get_bind()
    linhas = conexao.execute(
        sa.text("SELECT codigo_ibge, nome FROM municipio")
    ).fetchall()
    for codigo, nome in linhas:
        conexao.execute(
            sa.text("UPDATE municipio SET nome_busca = :busca WHERE codigo_ibge = :codigo"),
            {"busca": normalizar_busca(nome), "codigo": codigo},
        )


def downgrade() -> None:
    """A regra antiga apagava o apóstrofo sem separador; recalcula com ela."""
    import unicodedata

    conexao = op.get_bind()
    linhas = conexao.execute(
        sa.text("SELECT codigo_ibge, nome FROM municipio")
    ).fetchall()
    for codigo, nome in linhas:
        antigo = " ".join(
            unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().lower().split()
        )
        conexao.execute(
            sa.text("UPDATE municipio SET nome_busca = :busca WHERE codigo_ibge = :codigo"),
            {"busca": antigo, "codigo": codigo},
        )
