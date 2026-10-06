from app.acesso import verificar_acesso


def test_verificar_acesso_e_um_no_op():
    assert verificar_acesso() is None


def test_rotas_de_enxoval_dependem_de_verificar_acesso():
    """Spec seção 7: todas as rotas /enxovais dependem de acesso.py.

    Hoje não faz nada; é o ponto único de encaixe do Keycloak."""
    from app.rotas import enxovais, linhas

    for router in (enxovais.router, linhas.router):
        funcoes = {d.dependency for d in router.dependencies}
        assert verificar_acesso in funcoes
