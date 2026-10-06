"""Erros de domínio, traduzidos para HTTP em main.py."""


class ErroDominio(Exception):
    """Erro previsto, com código estável e mensagem em português para a pessoa."""

    status = 422

    def __init__(self, codigo: str, mensagem: str) -> None:
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem


class EnxovalNaoEncontrado(ErroDominio):
    status = 404

    def __init__(self) -> None:
        super().__init__(
            "enxoval_nao_encontrado",
            "Enxoval não encontrado. Confira o link ou comece um novo.",
        )


class DadoInvalido(ErroDominio):
    status = 422
