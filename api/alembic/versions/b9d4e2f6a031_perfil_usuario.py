"""Foto privada do perfil do usuário."""
from alembic import op
import sqlalchemy as sa

revision = "b9d4e2f6a031"
down_revision = "a8c3f1d2e945"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table("perfil_usuario", sa.Column("dono_id", sa.String(255), primary_key=True),
                    sa.Column("foto", sa.LargeBinary(), nullable=False))


def downgrade():
    op.drop_table("perfil_usuario")
