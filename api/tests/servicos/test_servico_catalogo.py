from app.db.enums import Faixa, PerfilCodigo, Prioridade, Tamanho, UsoClima
from app.motor.tipos import Catalogo
from app.servicos.catalogo import carregar_catalogo, perfis_por_codigo


def test_catalogo_do_banco_tem_tudo_que_o_motor_precisa(catalogo_no_banco):
    catalogo = carregar_catalogo(catalogo_no_banco)

    assert isinstance(catalogo, Catalogo)
    assert len(catalogo.itens) == 47
    assert len(catalogo.categorias) == 7
    assert len(catalogo.fases) == 8
    assert len(catalogo.janelas) == 5
    assert len(catalogo.regras_seguranca) == 8


def test_item_vem_com_tamanhos_regras_marcas_e_seguranca(catalogo_no_banco):
    catalogo = carregar_catalogo(catalogo_no_banco)

    body = next(i for i in catalogo.itens if i.slug == "body")
    assert {t.tamanho: t.quantidade_base for t in body.tamanhos} == {
        Tamanho.RN: 4, Tamanho.P: 8, Tamanho.M: 7, Tamanho.G: 6, Tamanho.GG: 6,
    }
    assert body.uso_clima == UsoClima.DIVIDE
    assert (body.variante_frio, body.variante_calor) == ("manga longa", "manga curta")
    assert body.escala_lavagem is True
    assert {t.tamanho: t.fase_codigo for t in body.tamanhos}[Tamanho.GG] == "bebe_6_9m"

    berco = next(i for i in catalogo.itens if i.slug == "berco")
    assert berco.e_seguranca is True
    assert [m.nome for m in berco.marcas][:2] == ["Tcil", "Reller"]
    assert all(m.faixa in Faixa for m in berco.marcas)
    assert "sono-seguro" in berco.regras_seguranca

    conforto = next(i for i in catalogo.itens if i.slug == "bebe-conforto")
    assert any(r.valor == Prioridade.UTIL.value for r in conforto.regras)


def test_itens_vem_na_ordem_de_categoria_e_item(catalogo_no_banco):
    catalogo = carregar_catalogo(catalogo_no_banco)

    ordem_categoria = {c.slug: c.ordem for c in catalogo.categorias}
    chaves = [(ordem_categoria[i.categoria_slug], i.ordem) for i in catalogo.itens]
    assert chaves == sorted(chaves)


def test_perfis_de_clima_viram_dataclasses(catalogo_no_banco):
    perfis = perfis_por_codigo(catalogo_no_banco)

    assert perfis[PerfilCodigo.FRIO].meses_frios == frozenset({5, 6, 7, 8, 9})
    assert perfis[PerfilCodigo.QUENTE].meses_frescos == frozenset({6, 7})
    assert len(perfis) == 3


def test_banco_sem_seed_devolve_catalogo_vazio_sem_quebrar(sessao):
    catalogo = carregar_catalogo(sessao)

    assert catalogo == Catalogo()


def test_carregar_catalogo_nao_dispara_consulta_por_item(catalogo_no_banco):
    """Sem eager loading, 47 itens virariam centenas de consultas."""
    from sqlalchemy import event

    consultas = []

    def registrar(conn, cursor, instrucao, *resto):
        consultas.append(instrucao)

    engine = catalogo_no_banco.get_bind()
    event.listen(engine, "before_cursor_execute", registrar)
    try:
        carregar_catalogo(catalogo_no_banco)
    finally:
        event.remove(engine, "before_cursor_execute", registrar)
    assert len(consultas) <= 12, f"{len(consultas)} consultas"
