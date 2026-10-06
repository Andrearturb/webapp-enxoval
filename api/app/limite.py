"""Limite simples de requisições por IP, em memória.

Vale por processo e zera quando a API reinicia; é defesa contra abuso acidental,
não contra ataque. Um limite de verdade (Redis ou no Caddy) fica para o deploy.
"""
import time
from collections import defaultdict, deque

from app.erros import ErroDominio


class MuitasRequisicoes(ErroDominio):
    status = 429

    def __init__(self) -> None:
        super().__init__(
            "muitas_requisicoes",
            "Você criou muitas listas em pouco tempo. Tente de novo mais tarde.",
        )


class LimitePorIp:
    def __init__(self, maximo: int, janela_segundos: int) -> None:
        self.maximo = maximo
        self.janela = janela_segundos
        self._marcas: dict[str, deque[float]] = defaultdict(deque)

    def verificar(self, ip: str, agora: float | None = None) -> None:
        agora = time.monotonic() if agora is None else agora
        marcas = self._marcas[ip]
        while marcas and agora - marcas[0] >= self.janela:
            marcas.popleft()
        if len(marcas) >= self.maximo:
            raise MuitasRequisicoes()
        marcas.append(agora)
