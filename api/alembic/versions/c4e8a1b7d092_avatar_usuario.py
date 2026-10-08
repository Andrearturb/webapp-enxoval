"""Avatares prontos, preservando fotos existentes."""
from alembic import op
import sqlalchemy as sa

revision = "c4e8a1b7d092"
down_revision = "b9d4e2f6a031"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("perfil_usuario", sa.Column("avatar", sa.String(32), nullable=True))
    op.alter_column("perfil_usuario", "foto", existing_type=sa.LargeBinary(), nullable=True)


def downgrade():
    # Recusar uma reversão que perderia escolhas feitas após a migração.
    if op.get_bind().execute(sa.text("SELECT count(*) FROM perfil_usuario WHERE foto IS NULL")).scalar():
        raise RuntimeError("Há perfis com avatar. Preserve ou remova essas escolhas antes de reverter a migração.")
    op.alter_column("perfil_usuario", "foto", existing_type=sa.LargeBinary(), nullable=False)
    op.drop_column("perfil_usuario", "avatar")
