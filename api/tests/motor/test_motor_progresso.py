from app.db.enums import Prioridade
from app.motor.progresso import Marcacao, progresso
from app.motor.tipos import LinhaCalculada


def _linha(chave: str, quantidade: int) -> LinhaCalculada:
    return LinhaCalculada(
        chave=chave, item_slug=chave.split(":")[0], nome="X", categoria_slug="c",
        tamanho=None, variante="", rotulo_variante=None, quantidade=quantidade,
        unidade_texto=None, prioridade=Prioridade.UTIL, fase_codigo="f",
        e_seguranca=False, escala_lavagem=False,
    )


def test_marcacao_soma_as_tres_origens():
    assert Marcacao(comprada=3, ganhada=4, ja_tinha=1).total == 8


def test_progresso_limita_cada_linha_a_sua_quantidade():
    linhas = [_linha("a::", 8), _linha("b::", 4)]
    marcadas = {
        "a::": Marcacao(comprada=3, ganhada=4, ja_tinha=3),  # 10 de 8: conta só 8
        "b::": Marcacao(comprada=1),
        "c::": Marcacao(ganhada=2),  # linha que saiu da lista
        "d::": Marcacao(),  # zerada: não conta como fora da lista
    }

    resultado = progresso(linhas, marcadas)

    assert resultado.total_unidades == 12
    assert resultado.atendidas == 9
    assert resultado.faltam == 3
    assert resultado.percentual == 75
    assert resultado.fora_da_lista == ("c::",)


def test_progresso_sem_marcacoes():
    resultado = progresso([_linha("a::", 5)], {})

    assert (resultado.atendidas, resultado.faltam, resultado.percentual) == (0, 5, 0)
    assert resultado.fora_da_lista == ()


def test_progresso_sem_linhas_nao_divide_por_zero():
    resultado = progresso([], {"x::": Marcacao(comprada=2)})

    assert (resultado.total_unidades, resultado.percentual) == (0, 0)
    assert resultado.fora_da_lista == ("x::",)
