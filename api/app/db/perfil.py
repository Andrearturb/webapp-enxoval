from sqlalchemy import LargeBinary, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PerfilUsuario(Base):
    """Avatar da conta; fotos antigas são mantidas até uma nova escolha."""

    __tablename__ = "perfil_usuario"
    dono_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    foto: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    avatar: Mapped[str | None] = mapped_column(String(32), nullable=True)
