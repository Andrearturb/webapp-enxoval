"""travas_catalogo

Revision ID: 78d8b021c91c
Revises: f17f5e46e3e3
Create Date: 2026-10-06 12:20:01.594698

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '78d8b021c91c'
down_revision: Union[str, Sequence[str], None] = 'f17f5e46e3e3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nome curto: op.create_check_constraint já aplica a convenção do projeto
    # (ck_<tabela>_<nome>) a partir de Base.metadata.naming_convention; passar o nome
    # já prefixado duplicava o prefixo (ck_<tabela>_ck_<tabela>_<nome>).
    op.create_check_constraint(
        "janela_com_duracao",
        "janela_tamanho",
        "idade_fim_dias > idade_inicio_dias",
    )
    op.create_check_constraint(
        "valor_de_prioridade_valido",
        "item_regra",
        "efeito <> 'mudar_prioridade' "
        "OR (valor IS NOT NULL AND valor IN ('essencial', 'util', 'pode_esperar'))",
    )


def downgrade() -> None:
    op.drop_constraint("ck_item_regra_valor_de_prioridade_valido", "item_regra")
    op.drop_constraint("ck_janela_tamanho_janela_com_duracao", "janela_tamanho")
