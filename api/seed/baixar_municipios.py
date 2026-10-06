"""Baixa a lista oficial de municípios do IBGE para dados/municipios.csv.

Uso único (o CSV vai para o git): docker compose run --rm api python -m seed.baixar_municipios
"""
import csv
import gzip
import json
import urllib.request

from seed.util import PASTA_DADOS

URL = "https://servicodados.ibge.gov.br/api/v1/localidades/municipios?view=nivelado"
ASSINATURA_GZIP = bytes([0x1F, 0x8B])


def main() -> None:
    with urllib.request.urlopen(URL, timeout=60) as resposta:
        corpo = resposta.read()
    if corpo[:2] == ASSINATURA_GZIP:  # o IBGE responde em gzip mesmo sem pedir
        corpo = gzip.decompress(corpo)
    dados = json.loads(corpo)
    linhas = sorted(
        (int(m["municipio-id"]), m["municipio-nome"], m["UF-sigla"]) for m in dados
    )
    with open(PASTA_DADOS / "municipios.csv", "w", encoding="utf-8", newline="") as arquivo:
        escritor = csv.writer(arquivo)
        escritor.writerow(["codigo_ibge", "nome", "uf"])
        escritor.writerows(linhas)
    print(f"{len(linhas)} municípios gravados")


if __name__ == "__main__":
    main()
