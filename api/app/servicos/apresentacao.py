"""Camada de apresentação: converte dados de domínio em schemas Pydantic HTTP.

Responsabilidade única: transformar as dataclasses imutáveis do motor e os modelos
ORM do banco nos contratos de saída HTTP — sem lógica de negócio além do cálculo de
``faltam``, que é derivação direta das quantidades marcadas.
"""
from app.db.catalogo import Municipio
from app.db.familia import Enxoval, EnxovalLinha
from app.rotas.schemas import (
    AlertaSaida,
    CategoriaSaida,
    EnxovalResumo,
    EnxovalSaida,
    FaseSaida,
    FichaSaida,
    LinhaForaSaida,
    LinhaSaida,
    MarcasSaida,
    MunicipioSaida,
    ProgressoSaida,
    RespostasSaida,
    ResumoSaida,
)
from app.servicos.leitura import EnxovalCompleto


def montar_saida(completo: EnxovalCompleto) -> EnxovalSaida:
    """Converte um EnxovalCompleto no schema de saída HTTP EnxovalSaida.

    Mescla as linhas calculadas pelo motor com as quantidades marcadas pela
    família e calcula ``faltam = max(0, quantidade − (comprada + ganhada + ja_tinha))``.

    Args:
        completo: Resultado completo da leitura do enxoval, contendo o modelo ORM,
            o enxoval calculado pelo motor, as marcações da família e o catálogo.

    Returns:
        EnxovalSaida pronto para serialização HTTP.
    """
    enxoval = completo.enxoval
    calculado = completo.calculado
    marcadas = completo.marcadas

    itens_por_slug = {item.slug: item for item in completo.catalogo.itens}

    def _fora_da_lista(linha: EnxovalLinha) -> LinhaForaSaida:
        slug, tamanho, variante = (linha.chave.split(":") + ["", ""])[:3]
        item = itens_por_slug.get(slug)
        rotulo = None
        if item and variante in ("frio", "calor"):
            rotulo = item.variante_frio if variante == "frio" else item.variante_calor
        return LinhaForaSaida(
            chave=linha.chave,
            nome=item.nome if item else slug.replace("-", " "),
            tamanho=tamanho or None,
            rotulo_variante=rotulo,
            comprada=linha.qtd_comprada,
            ganhada=linha.qtd_ganhada,
            ja_tinha=linha.qtd_ja_tinha,
        )

    def _quantidades(chave: str) -> tuple[int, int, int]:
        """Retorna (comprada, ganhada, ja_tinha) para uma chave, ou (0, 0, 0) se ausente."""
        marca = marcadas.get(chave)
        return (marca.comprada, marca.ganhada, marca.ja_tinha) if marca else (0, 0, 0)

    linhas = []
    for linha in calculado.linhas:
        comprada, ganhada, ja_tinha = _quantidades(linha.chave)
        linhas.append(
            LinhaSaida(
                chave=linha.chave,
                item_slug=linha.item_slug,
                nome=linha.nome,
                rotulo_variante=linha.rotulo_variante,
                categoria_slug=linha.categoria_slug,
                tamanho=linha.tamanho,
                quantidade=linha.quantidade,
                unidade_texto=linha.unidade_texto,
                prioridade=linha.prioridade,
                fase_codigo=linha.fase_codigo,
                e_seguranca=linha.e_seguranca,
                comprada=comprada,
                ganhada=ganhada,
                ja_tinha=ja_tinha,
                faltam=max(0, linha.quantidade - (comprada + ganhada + ja_tinha)),
                momento_compra=linha.momento_compra,
            )
        )

    return EnxovalSaida(
        id=enxoval.id,
        respostas=RespostasSaida(
            municipio=MunicipioSaida(
                codigo_ibge=completo.municipio.codigo_ibge,
                nome=completo.municipio.nome,
                uf=completo.municipio.uf,
            ),
            perfil_clima=enxoval.perfil_clima,
            perfil_corrigido=enxoval.perfil_corrigido,
            data_prevista=enxoval.data_prevista,
            dias_entre_lavagens=enxoval.dias_entre_lavagens,
            moradia=enxoval.moradia,
            tem_carro=enxoval.tem_carro,
            orcamento=enxoval.orcamento,
            primeiro_filho=enxoval.primeiro_filho,
        ),
        categorias=[
            CategoriaSaida(slug=c.slug, nome=c.nome, ordem=c.ordem)
            for c in completo.catalogo.categorias
        ],
        linhas=linhas,
        linhas_fora_da_lista=[_fora_da_lista(l) for l in completo.fora_da_lista],
        fichas=[
            FichaSaida(
                slug=f.slug,
                nome=f.nome,
                para_que_serve=f.para_que_serve,
                como_escolher=f.como_escolher,
                idade_inicio_meses=f.idade_inicio_meses,
                marcas=MarcasSaida(
                    nomes=list(f.marcas.nomes),
                    faixa=f.marcas.faixa,
                    faixa_aproximada=f.marcas.fallback,
                ),
                dicas=list(f.dicas),
                regras_seguranca=list(f.regras_seguranca),
            )
            for f in calculado.fichas
        ],
        roteiro=[
            FaseSaida(
                codigo=f.codigo,
                nome=f.nome,
                texto=f.texto,
                inicio=f.inicio,
                fim=f.fim,
                atual=f.atual,
            )
            for f in calculado.roteiro
        ],
        alertas=[
            AlertaSaida(
                codigo=a.codigo,
                tema=a.tema,
                texto=a.texto,
                base=a.base,
                ativo_a_partir=a.ativo_a_partir,
                ativo_ate=a.ativo_ate,
                itens=list(a.itens),
            )
            for a in calculado.alertas
        ],
        resumo=ResumoSaida(
            dias_sem_lavar=calculado.resumo.dias_sem_lavar,
            total_unidades=calculado.resumo.total_unidades,
            aviso_volume_alto=calculado.resumo.aviso_volume_alto,
            destacar_ja_tinha=calculado.resumo.destacar_ja_tinha,
        ),
        progresso=ProgressoSaida(
            total_unidades=completo.progresso.total_unidades,
            atendidas=completo.progresso.atendidas,
            faltam=completo.progresso.faltam,
            percentual=completo.progresso.percentual,
        ),
    )


def montar_resumo(enxoval: Enxoval, municipio: Municipio | None, percentual: int) -> EnxovalResumo:
    """Converte um Enxoval ORM num resumo leve para a tela 'Meus enxovais'.

    Args:
        enxoval: Instância ORM do enxoval (sem linhas carregadas).
        municipio: Instância ORM do município (pode ser None se removido).
        percentual: Percentual de progresso pré-calculado (0-100).

    Returns:
        ``EnxovalResumo`` pronto para serialização HTTP.
    """
    return EnxovalResumo(
        id=enxoval.id,
        municipio_nome=municipio.nome if municipio else "—",
        municipio_uf=municipio.uf if municipio else "—",
        data_prevista=enxoval.data_prevista,
        percentual_progresso=percentual,
    )
