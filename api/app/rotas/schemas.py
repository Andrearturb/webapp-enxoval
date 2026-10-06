"""Contrato HTTP: o que entra e o que sai. Nomes pensados para a tela, não para o banco."""
import uuid
from datetime import date

from pydantic import BaseModel, Field

from app.db.enums import Faixa, Moradia, PerfilCodigo, Prioridade, Tamanho, TemaSeguranca
from app.servicos.escrita import DadosRespostas
from app.servicos.leitura import EnxovalCompleto


class Erro(BaseModel):
    erro: str
    mensagem: str


# ---------- entrada ----------


class RespostasEntrada(BaseModel):
    municipio_codigo: int = Field(gt=0)
    data_prevista: date
    dias_entre_lavagens: int = Field(ge=1, le=7)
    moradia: Moradia
    tem_carro: bool
    orcamento: Faixa
    primeiro_filho: bool
    correcao_perfil: PerfilCodigo | None = None

    def para_servico(self) -> DadosRespostas:
        return DadosRespostas(**self.model_dump())


class MarcacaoEntrada(BaseModel):
    comprada: int = Field(ge=0)
    ganhada: int = Field(ge=0)
    ja_tinha: int = Field(ge=0)


class CompletarEntrada(BaseModel):
    origem: str = Field(pattern="^(comprada|ganhada|ja_tinha)$")


# ---------- saída ----------


class MunicipioSaida(BaseModel):
    codigo_ibge: int
    nome: str
    uf: str


class PerfilSaida(BaseModel):
    codigo: PerfilCodigo
    nome: str
    descricao: str
    meses_frios: list[int]
    meses_frescos: list[int]


class RespostasSaida(BaseModel):
    municipio: MunicipioSaida
    perfil_clima: PerfilCodigo
    perfil_corrigido: bool
    data_prevista: date
    dias_entre_lavagens: int
    moradia: Moradia
    tem_carro: bool
    orcamento: Faixa
    primeiro_filho: bool


class CategoriaSaida(BaseModel):
    slug: str
    nome: str
    ordem: int


class LinhaSaida(BaseModel):
    chave: str
    item_slug: str
    nome: str
    rotulo_variante: str | None
    categoria_slug: str
    tamanho: Tamanho | None
    quantidade: int
    unidade_texto: str | None
    prioridade: Prioridade
    fase_codigo: str
    e_seguranca: bool
    comprada: int
    ganhada: int
    ja_tinha: int
    faltam: int


class LinhaForaSaida(BaseModel):
    chave: str
    comprada: int
    ganhada: int
    ja_tinha: int


class MarcasSaida(BaseModel):
    nomes: list[str]
    faixa: Faixa | None
    faixa_aproximada: bool


class FichaSaida(BaseModel):
    slug: str
    nome: str
    para_que_serve: str
    como_escolher: str
    idade_inicio_meses: int
    marcas: MarcasSaida
    dicas: list[str]
    regras_seguranca: list[str]


class FaseSaida(BaseModel):
    codigo: str
    nome: str
    texto: str
    inicio: date
    fim: date
    atual: bool


class AlertaSaida(BaseModel):
    codigo: str
    tema: TemaSeguranca
    texto: str
    base: str
    ativo_a_partir: date
    ativo_ate: date
    itens: list[str]


class ResumoSaida(BaseModel):
    dias_sem_lavar: int
    total_unidades: int
    aviso_volume_alto: bool
    destacar_ja_tinha: bool


class ProgressoSaida(BaseModel):
    total_unidades: int
    atendidas: int
    faltam: int
    percentual: int


class EnxovalSaida(BaseModel):
    id: uuid.UUID
    respostas: RespostasSaida
    categorias: list[CategoriaSaida]
    linhas: list[LinhaSaida]
    linhas_fora_da_lista: list[LinhaForaSaida]
    fichas: list[FichaSaida]
    roteiro: list[FaseSaida]
    alertas: list[AlertaSaida]
    resumo: ResumoSaida
    progresso: ProgressoSaida


class EnxovalCriado(BaseModel):
    id: uuid.UUID


def montar_saida(completo: EnxovalCompleto) -> EnxovalSaida:
    enxoval, calculado = completo.enxoval, completo.calculado
    marcadas = completo.marcadas
    vazia = (0, 0, 0)

    def quantidades(chave: str) -> tuple[int, int, int]:
        marca = marcadas.get(chave)
        return (marca.comprada, marca.ganhada, marca.ja_tinha) if marca else vazia

    linhas = []
    for linha in calculado.linhas:
        comprada, ganhada, ja_tinha = quantidades(linha.chave)
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
        linhas_fora_da_lista=[
            LinhaForaSaida(
                chave=l.chave,
                comprada=l.qtd_comprada,
                ganhada=l.qtd_ganhada,
                ja_tinha=l.qtd_ja_tinha,
            )
            for l in completo.fora_da_lista
        ],
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
                codigo=f.codigo, nome=f.nome, texto=f.texto,
                inicio=f.inicio, fim=f.fim, atual=f.atual,
            )
            for f in calculado.roteiro
        ],
        alertas=[
            AlertaSaida(
                codigo=a.codigo, tema=a.tema, texto=a.texto, base=a.base,
                ativo_a_partir=a.ativo_a_partir, ativo_ate=a.ativo_ate,
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
