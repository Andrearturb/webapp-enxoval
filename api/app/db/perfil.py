from sqlalchemy import LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PerfilUsuario(Base):
    """Foto privada da conta; nome, e-mail e credenciais pertencem ao Keycloak."""

    __tablename__ = "perfil_usuario"
    dono_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    foto: Mapped[bytes] = mapped_column(LargeBinary)
