"""Importa todos os módulos de modelos para registrá-los em Base.metadata.

O Alembic (env.py) importa este arquivo. Cada novo módulo de modelos entra aqui.
"""
from app.db import catalogo  # noqa: F401
from app.db import familia  # noqa: F401
