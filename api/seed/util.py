from enum import StrEnum
from pathlib import Path
from typing import Any

import yaml
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

PASTA_DADOS = Path(__file__).parent / "dados"


def ler_yaml(nome: str) -> Any:
    with open(PASTA_DADOS / nome, encoding="utf-8") as arquivo:
        return yaml.safe_load(arquivo)


def inserir_se_faltar(
    sessao: Session, modelo: type, linhas: list[dict], chave: list[str]
) -> int:
    """Insere as linhas que ainda não existem (pela chave). Nunca sobrescreve."""
    if not linhas:
        return 0
    tabela = modelo.__table__
    comando = (
        pg_insert(tabela)
        .values(linhas)
        .on_conflict_do_nothing(index_elements=chave)
        .returning(*tabela.primary_key.columns)
    )
    # rowcount vale -1 neste driver; RETURNING só devolve as linhas realmente inseridas.
    return len(sessao.execute(comando).all())


def enum_de[E: StrEnum](enum_cls: type[E], valor: Any, contexto: str) -> E:
    try:
        return enum_cls(valor)
    except ValueError:
        validos = ", ".join(m.value for m in enum_cls)
        raise ValueError(
            f"{contexto}: valor '{valor}' inválido; use um de: {validos}"
        ) from None


def buscar(mapa: dict, chave: Any, contexto: str, tipo: str) -> Any:
    try:
        return mapa[chave]
    except KeyError:
        raise ValueError(f"{contexto}: {tipo} '{chave}' não encontrado(a)") from None


def validar_campos(bruto: dict, obrigatorios: set[str], opcionais: set[str], contexto: str) -> None:
    """Recusa campo obrigatório ausente e campo desconhecido (erro de digitação no YAML)."""
    ausentes = sorted(obrigatorios - bruto.keys())
    if ausentes:
        raise ValueError(f"{contexto}: campo obrigatório ausente: {', '.join(ausentes)}")
    desconhecidos = sorted(bruto.keys() - obrigatorios - opcionais)
    if desconhecidos:
        validos = ", ".join(sorted(obrigatorios | opcionais))
        raise ValueError(
            f"{contexto}: campo desconhecido: {', '.join(desconhecidos)}; válidos: {validos}"
        )
