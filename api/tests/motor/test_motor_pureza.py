import subprocess
import sys
from pathlib import Path

RAIZ_API = Path(__file__).resolve().parents[2]

PROIBIDOS = ("sqlalchemy", "fastapi", "starlette", "psycopg", "alembic")


def test_motor_nao_importa_banco_nem_http():
    """Importa todos os módulos de app.motor num processo limpo e inspeciona sys.modules."""
    codigo = (
        "import importlib, pkgutil, sys\n"
        "import app.motor as pacote\n"
        "for modulo in pkgutil.iter_modules(pacote.__path__):\n"
        "    importlib.import_module('app.motor.' + modulo.name)\n"
        f"proibidos = [n for n in sys.modules if n.split('.')[0] in {PROIBIDOS!r}]\n"
        "assert not proibidos, proibidos\n"
    )
    resultado = subprocess.run(
        [sys.executable, "-c", codigo], capture_output=True, text=True, cwd=RAIZ_API
    )
    assert resultado.returncode == 0, resultado.stderr
