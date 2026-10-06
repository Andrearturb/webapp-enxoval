import math
from fractions import Fraction


def fator_lavagem(dias_entre_lavagens: int) -> Fraction:
    """(dias + 1) / 3. As quantidades-base do catálogo são calibradas para lavar a cada 2 dias."""
    if not 1 <= dias_entre_lavagens <= 7:
        raise ValueError(
            f"dias entre lavagens deve ficar entre 1 e 7 (recebido: {dias_entre_lavagens})"
        )
    return Fraction(dias_entre_lavagens + 1, 3)


def quantidade(base: int, fator: Fraction) -> int:
    if base < 0:
        raise ValueError(f"a quantidade base não pode ser negativa (recebido: {base})")
    return math.ceil(base * fator)


def dividir_variantes(total: int, proporcao_frio: Fraction) -> tuple[int, int]:
    """Divide `total` em (frio, calor), sem perder nem criar peças. Meio arredonda para cima."""
    if total < 0:
        raise ValueError(f"a quantidade total não pode ser negativa (recebido: {total})")
    if not 0 <= proporcao_frio <= 1:
        raise ValueError(f"a proporção de frio deve ficar entre 0 e 1 (recebido: {proporcao_frio})")
    frio = math.floor(total * proporcao_frio + Fraction(1, 2))
    return frio, total - frio
