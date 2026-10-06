from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from app.motor.tipos import LinhaCalculada


@dataclass(frozen=True)
class Marcacao:
    comprada: int = 0
    ganhada: int = 0
    ja_tinha: int = 0

    @property
    def total(self) -> int:
        return self.comprada + self.ganhada + self.ja_tinha


@dataclass(frozen=True)
class Progresso:
    total_unidades: int
    atendidas: int
    faltam: int
    percentual: int
    fora_da_lista: tuple[str, ...]


def progresso(linhas: Iterable[LinhaCalculada], marcadas: Mapping[str, Marcacao]) -> Progresso:
    """Quanto da lista já está atendido. Uma linha nunca conta além da própria quantidade."""
    linhas = list(linhas)
    total = sum(l.quantidade for l in linhas)
    atendidas = sum(
        min(l.quantidade, marcadas[l.chave].total) for l in linhas if l.chave in marcadas
    )
    chaves = {l.chave for l in linhas}
    fora = tuple(sorted(c for c, m in marcadas.items() if c not in chaves and m.total > 0))
    return Progresso(
        total_unidades=total,
        atendidas=atendidas,
        faltam=total - atendidas,
        percentual=(100 * atendidas) // total if total else 0,
        fora_da_lista=fora,
    )
