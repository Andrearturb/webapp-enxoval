from datetime import date, timedelta
from fractions import Fraction

from app.db.enums import PerfilCodigo
from app.motor.tipos import PerfilClima

PONTOS_MES_FRIO = 2  # contamos em meios-dias para manter tudo em números inteiros
PONTOS_MES_FRESCO = 1


def resolver_perfil(
    excecao_do_municipio: PerfilCodigo | None,
    padrao_do_estado: PerfilCodigo,
    correcao: PerfilCodigo | None,
) -> PerfilCodigo:
    """Correção da família > exceção do município > padrão do estado."""
    return correcao or excecao_do_municipio or padrao_do_estado


def proporcao_frio(
    data_prevista: date,
    inicio_dias: int,
    fim_dias: int,
    perfil: PerfilClima,
    incluir_frescos: bool = True,
) -> Fraction:
    """Fração (0 a 1) da janela [inicio_dias, fim_dias) que cai em mês frio.

    Cada dia conta pelo mês em que cai: mês frio vale 1, mês fresco vale 1/2 (se
    `incluir_frescos`) e os demais valem 0. A idade do bebê é contada a partir da data prevista.
    """
    total = fim_dias - inicio_dias
    if total <= 0:
        raise ValueError(f"janela inválida: de {inicio_dias} a {fim_dias} dias")
    pontos = 0
    for dia in range(inicio_dias, fim_dias):
        mes = (data_prevista + timedelta(days=dia)).month
        if mes in perfil.meses_frios:
            pontos += PONTOS_MES_FRIO
        elif incluir_frescos and mes in perfil.meses_frescos:
            pontos += PONTOS_MES_FRESCO
    return Fraction(pontos, PONTOS_MES_FRIO * total)
