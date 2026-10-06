import re
import unicodedata

NAO_ALFANUMERICO = re.compile(r"[^0-9A-Za-z]+")


def normalizar_busca(texto: str) -> str:
    """Minúsculas, sem acento, e tudo que não é letra ou número vira espaço.

    Apóstrofo reto, apóstrofo tipográfico e hífen viram separador, para que
    "Olhos-d'Água", "Olhos d Agua" e "olhos d agua" cheguem ao mesmo texto.
    """
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c)
    )
    return " ".join(NAO_ALFANUMERICO.sub(" ", sem_acento).lower().split())
