"""Carrega o conteúdo no banco: docker compose run --rm api python -m seed [--forcar]"""
import sys

from sqlalchemy.orm import Session

from app.db.sessao import obter_engine
from seed.carregar import carregar_tudo


def main() -> None:
    forcar = "--forcar" in sys.argv[1:]
    with Session(obter_engine()) as sessao, sessao.begin():
        resumo = carregar_tudo(sessao, forcar=forcar)
    for tabela, novas in resumo.items():
        print(f"{tabela}: {novas} novo(s)")


if __name__ == "__main__":
    main()
