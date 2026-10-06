import os
from datetime import date

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session

URL_TESTE = os.environ["TEST_DATABASE_URL"]


@pytest.fixture(scope="session")
def engine_teste():
    """Banco de teste zerado e migrado uma vez por execução do pytest."""
    engine = create_engine(URL_TESTE)
    with engine.begin() as conexao:
        conexao.execute(text("DROP SCHEMA public CASCADE"))
        conexao.execute(text("CREATE SCHEMA public"))
    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", URL_TESTE.replace("%", "%%"))
    command.upgrade(cfg, "head")
    yield engine
    engine.dispose()


@pytest.fixture
def sessao(engine_teste):
    """Sessão cujo trabalho é desfeito no fim de cada teste."""
    conexao = engine_teste.connect()
    transacao = conexao.begin()
    sessao = Session(bind=conexao, join_transaction_mode="create_savepoint")
    yield sessao
    sessao.close()
    transacao.rollback()
    conexao.close()


@pytest.fixture
def catalogo_no_banco(sessao):
    """Conteúdo do catálogo no banco, sem os 5.571 municípios (carga de ~0,35 s).

    Fica dentro da transação do teste, então não interfere nos testes de carga.
    """
    from app.db.catalogo import Estado, Municipio
    from app.db.enums import PerfilCodigo
    from app.texto import normalizar_busca
    from seed.base import carregar_base
    from seed.itens import carregar_itens, carregar_marcas
    from seed.seguranca import carregar_seguranca

    carregar_base(sessao)
    carregar_marcas(sessao)
    carregar_itens(sessao)
    carregar_seguranca(sessao)
    cidades = [
        (4106902, "Curitiba", "PR", None),
        (2927408, "Salvador", "BA", None),
        (3550308, "São Paulo", "SP", None),
        (4302105, "Bom Jesus", "RS", PerfilCodigo.MODERADO),  # difere do padrão do RS (frio)
        (2202075, "Bom Jesus", "PI", None),
        (1100015, "Alta Floresta D'Oeste", "RO", None),
    ]
    ufs = {uf for _, _, uf, _ in cidades}
    existentes = {e.uf for e in sessao.query(Estado).filter(Estado.uf.in_(ufs))}
    for uf in ufs - existentes:  # os estados já vêm do carregar_base
        raise AssertionError(f"estado {uf} não foi carregado pelo seed")
    for codigo, nome, uf, excecao in cidades:
        sessao.add(
            Municipio(
                codigo_ibge=codigo, nome=nome, nome_busca=normalizar_busca(nome),
                uf=uf, perfil_excecao=excecao,
            )
        )
    sessao.flush()
    return sessao


HOJE_FIXO = date(2027, 2, 1)


@pytest.fixture
def cliente(sessao):
    """TestClient com a sessão do teste e uma data de hoje fixa."""
    from fastapi.testclient import TestClient

    from app.config import Configuracoes
    from app.db.sessao import obter_sessao
    from app.dependencias import obter_hoje
    from app.limite import LimitePorIp
    from app.main import criar_app
    from app.rotas import enxovais as rotas_enxovais

    app = criar_app(Configuracoes(database_url=URL_TESTE))
    app.dependency_overrides[obter_sessao] = lambda: sessao
    app.dependency_overrides[obter_hoje] = lambda: HOJE_FIXO
    # O limite de criação é um singleton por processo; sem resetar aqui, os testes
    # se acumulariam no mesmo limite e um teste posterior receberia 429 por engano.
    rotas_enxovais.limite_de_criacao = LimitePorIp(
        rotas_enxovais.MAXIMO_CRIACOES, rotas_enxovais.JANELA_SEGUNDOS
    )
    return TestClient(app, raise_server_exceptions=False)
