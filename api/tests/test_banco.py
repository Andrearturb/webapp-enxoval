from sqlalchemy import text


def test_migracoes_aplicadas_no_banco_de_teste(sessao):
    versoes = sessao.execute(text("SELECT count(*) FROM alembic_version")).scalar_one()
    assert versoes == 1
