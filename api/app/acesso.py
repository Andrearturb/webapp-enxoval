"""Ponto único de encaixe do controle de acesso (spec seção 7).

Hoje não faz nada: até o Keycloak chegar, o UUID do enxoval é a própria chave
de acesso. Quando o realm existir, `verificar_acesso` passa a validar o token
e filtrar pelo dono — sem precisar tocar cada rota de `/enxovais` de novo.
"""


def verificar_acesso() -> None:
    pass
