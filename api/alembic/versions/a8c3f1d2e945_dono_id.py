"""dono_id — coluna de proprietário para autenticação Keycloak

Adiciona ``dono_id`` na tabela ``enxoval`` para armazenar o ``sub``
(subject) do token JWT emitido pelo Keycloak.

Coluna nullable nesta migration para não quebrar instâncias existentes.
Em produção com banco zerado ela nunca terá NULL — o NOT NULL será
adicionado numa migration posterior após o deploy com auth obrigatório.

Revision ID: a8c3f1d2e945
Revises: 697b0a342a50
Create Date: 2026-10-07 12:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a8c3f1d2e945'
down_revision: Union[str, Sequence[str], None] = '697b0a342a50'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Adiciona coluna dono_id e índice para busca por proprietário."""
    op.add_column(
        'enxoval',
        sa.Column('dono_id', sa.String(255), nullable=True),
    )
    op.create_index('ix_enxoval_dono_id', 'enxoval', ['dono_id'])


def downgrade() -> None:
    """Remove coluna dono_id e índice."""
    op.drop_index('ix_enxoval_dono_id', table_name='enxoval')
    op.drop_column('enxoval', 'dono_id')
