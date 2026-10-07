"""Rótulos de exibição para enums de domínio usados nos exportadores.

Centraliza as traduções de ``Prioridade`` e ``MomentoCompra`` para evitar
duplicação entre os geradores CSV, XLSX e PDF.
"""
from typing import Final

# Rótulos legíveis para o campo ``prioridade`` de cada linha da planilha.
PRIORIDADE: Final[dict[str, str]] = {
    "essencial": "Essencial",
    "util": "Útil",
    "pode_esperar": "Pode esperar",
}

# Rótulos legíveis para o campo ``momento_compra`` de cada linha da planilha.
MOMENTO_COMPRA: Final[dict[str, str]] = {
    "atrasado": "⚠ Atrasado",
    "agora": "Agora",
    "proxima_fase": "Próxima fase",
    "futuro": "Mais para frente",
}
