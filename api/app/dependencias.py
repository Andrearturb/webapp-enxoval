"""Dependências do FastAPI que os testes sobrescrevem."""
from datetime import date


def obter_hoje() -> date:
    """O único lugar do projeto, fora dos testes, que lê o relógio.

    O motor recebe a data como parâmetro justamente para não depender do relógio.
    """
    return date.today()
