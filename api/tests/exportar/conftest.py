"""Fixture compartilhada para os testes de exportação.

Usa EnxovalSaida diretamente — sem banco, sem motor, sem seed.
"""
import uuid
from datetime import date

import pytest

from app.db.enums import Faixa, MomentoCompra, Moradia, PerfilCodigo, Prioridade, TemaSeguranca
from app.rotas.schemas import (
    AlertaSaida,
    CategoriaSaida,
    EnxovalSaida,
    FaseSaida,
    FichaSaida,
    LinhaSaida,
    MarcasSaida,
    ProgressoSaida,
    RespostasSaida,
    ResumoSaida,
    MunicipioSaida,
)


@pytest.fixture
def saida_exemplo() -> EnxovalSaida:
    """Enxoval mínimo mas realista para testar os geradores de arquivo."""
    return EnxovalSaida(
        id=uuid.UUID("00000000-0000-0000-0000-000000000001"),
        respostas=RespostasSaida(
            municipio=MunicipioSaida(codigo_ibge=4106902, nome="Curitiba", uf="PR"),
            perfil_clima=PerfilCodigo.FRIO,
            perfil_corrigido=False,
            data_prevista=date(2027, 6, 1),
            dias_entre_lavagens=2,
            moradia=Moradia.APARTAMENTO,
            tem_carro=True,
            orcamento=Faixa.INTERMEDIARIO,
            primeiro_filho=True,
        ),
        categorias=[
            CategoriaSaida(slug="roupas", nome="Roupas", ordem=1),
            CategoriaSaida(slug="higiene", nome="Higiene", ordem=2),
        ],
        linhas=[
            LinhaSaida(
                chave="body:P:",
                item_slug="body",
                nome="Body",
                rotulo_variante=None,
                categoria_slug="roupas",
                tamanho="P",
                quantidade=8,
                unidade_texto=None,
                prioridade=Prioridade.ESSENCIAL,
                fase_codigo="gestacao_7_8m",
                e_seguranca=False,
                comprada=3,
                ganhada=0,
                ja_tinha=0,
                faltam=5,
                momento_compra=MomentoCompra.AGORA,
            ),
            LinhaSaida(
                chave="macacao:RN:",
                item_slug="macacao",
                nome="Macacão",
                rotulo_variante=None,
                categoria_slug="roupas",
                tamanho="RN",
                quantidade=4,
                unidade_texto=None,
                prioridade=Prioridade.ESSENCIAL,
                fase_codigo="gestacao_7_8m",
                e_seguranca=False,
                comprada=4,
                ganhada=0,
                ja_tinha=0,
                faltam=0,
                momento_compra=MomentoCompra.AGORA,
            ),
            LinhaSaida(
                chave="fralda::",
                item_slug="fralda",
                nome="Fralda descartável",
                rotulo_variante=None,
                categoria_slug="higiene",
                tamanho=None,
                quantidade=4,
                unidade_texto="pacotes",
                prioridade=Prioridade.ESSENCIAL,
                fase_codigo="gestacao_7_8m",
                e_seguranca=False,
                comprada=2,
                ganhada=0,
                ja_tinha=0,
                faltam=2,
                momento_compra=MomentoCompra.AGORA,
            ),
        ],
        linhas_fora_da_lista=[],
        fichas=[
            FichaSaida(
                slug="body",
                nome="Body",
                para_que_serve="Roupa base do bebê.",
                como_escolher="Algodão, zíper ou botões na frente.",
                idade_inicio_meses=0,
                marcas=MarcasSaida(nomes=["Hering", "Carter's"], faixa=Faixa.INTERMEDIARIO, faixa_aproximada=False),
                dicas=["Compre mais tamanho P do que RN."],
                regras_seguranca=[],
            )
        ],
        roteiro=[
            FaseSaida(
                codigo="gestacao_7_8m",
                nome="7º–8º mês de gestação",
                texto="Comprar roupas RN e P.",
                inicio=date(2027, 2, 1),
                fim=date(2027, 4, 30),
                atual=True,
            ),
            FaseSaida(
                codigo="bebe_0_3m",
                nome="0–3 meses",
                texto="Repor fraldas.",
                inicio=date(2027, 6, 1),
                fim=date(2027, 8, 31),
                atual=False,
            ),
        ],
        alertas=[
            AlertaSaida(
                codigo="sono_seguro",
                tema=TemaSeguranca.SONO,
                texto="Dormir de barriga para cima.",
                base="SBP",
                ativo_a_partir=date(2027, 6, 1),
                ativo_ate=date(2028, 6, 1),
                itens=[],
            )
        ],
        resumo=ResumoSaida(
            dias_sem_lavar=2,
            total_unidades=16,
            aviso_volume_alto=False,
            destacar_ja_tinha=False,
        ),
        progresso=ProgressoSaida(
            total_unidades=16,
            atendidas=9,
            faltam=7,
            percentual=56,
        ),
    )
