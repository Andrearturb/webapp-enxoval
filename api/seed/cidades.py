import csv

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.catalogo import Municipio
from app.db.enums import PerfilCodigo
from app.texto import normalizar_busca
from seed.util import PASTA_DADOS, enum_de, inserir_se_faltar, ler_yaml

TAMANHO_LOTE = 1000


def carregar_municipios(sessao: Session) -> int:
    with open(PASTA_DADOS / "municipios.csv", encoding="utf-8", newline="") as arquivo:
        linhas = [
            {
                "codigo_ibge": int(linha["codigo_ibge"]),
                "nome": linha["nome"],
                "nome_busca": normalizar_busca(linha["nome"]),
                "uf": linha["uf"],
            }
            for linha in csv.DictReader(arquivo)
        ]
    return sum(
        inserir_se_faltar(sessao, Municipio, linhas[i : i + TAMANHO_LOTE], ["codigo_ibge"])
        for i in range(0, len(linhas), TAMANHO_LOTE)
    )


def aplicar_excecoes(sessao: Session, dados: list | None = None) -> int:
    """Marca o perfil de exceção, sem mexer em município já marcado (pelo admin)."""
    dados = dados if dados is not None else ler_yaml("excecoes_municipios.yaml")
    aplicadas = 0
    for bruto in dados:
        ctx = f"exceção '{bruto['nome']}/{bruto['uf']}'"
        municipio = sessao.scalars(
            select(Municipio).where(
                Municipio.nome_busca == normalizar_busca(bruto["nome"]),
                Municipio.uf == bruto["uf"],
            )
        ).one_or_none()
        if municipio is None:
            raise ValueError(f"{ctx}: município não encontrado")
        if municipio.perfil_excecao is None:
            municipio.perfil_excecao = enum_de(PerfilCodigo, bruto["perfil"], ctx)
            aplicadas += 1
    sessao.flush()
    return aplicadas
