"""Redige UUIDs de todo log do processo.

O UUID do enxoval é a chave de acesso de facto (spec seção 7: "Até lá, o UUID v4
funciona como chave de acesso"). Nunca pode aparecer em log — nem na mensagem de
erro, nem no access log do uvicorn, nem na pilha de uma exceção inesperada.

Atua na fábrica de `LogRecord`, antes de qualquer logger ou handler: um
`logging.Filter` anexado a um logger só é consultado pelo logger de origem da
chamada, nunca por loggers ancestrais durante a propagação, então não cobriria
os loggers de cada módulo (`app.main`, futuros módulos etc.) a partir de um só
ponto. A fábrica, em vez disso, intercepta todo registro no nascimento.
"""
import logging
import re

PADRAO_UUID = re.compile(
    r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}"
)

_instalado = False


def _redigir(texto: str) -> str:
    return PADRAO_UUID.sub("[uuid]", texto)


def redigir_registro(registro: logging.LogRecord) -> logging.LogRecord:
    """Redige em lugar: mensagem, argumentos e a pilha de uma exceção, se houver."""
    if isinstance(registro.msg, str):
        registro.msg = _redigir(registro.msg)
    if registro.args:
        if isinstance(registro.args, dict):
            registro.args = {
                chave: _redigir(valor) if isinstance(valor, str) else valor
                for chave, valor in registro.args.items()
            }
        else:
            registro.args = tuple(
                _redigir(arg) if isinstance(arg, str) else arg
                for arg in registro.args
            )
    if registro.exc_info:
        texto = logging.Formatter().formatException(registro.exc_info)
        if PADRAO_UUID.search(texto):
            # Gera e redige a pilha aqui; limpar exc_info evita que o Formatter
            # a gere de novo (sem redação) ao formatar o registro.
            registro.exc_text = _redigir(texto)
            registro.exc_info = None
    return registro


def instalar_redator_de_uuid() -> None:
    """Troca a fábrica de `LogRecord` do processo por uma que redige UUIDs.

    Idempotente: chamar de novo não encadeia fábricas repetidas.
    """
    global _instalado
    if _instalado:
        return
    fabrica_original = logging.getLogRecordFactory()

    def fabrica(*args, **kwargs) -> logging.LogRecord:
        return redigir_registro(fabrica_original(*args, **kwargs))

    logging.setLogRecordFactory(fabrica)
    _instalado = True
