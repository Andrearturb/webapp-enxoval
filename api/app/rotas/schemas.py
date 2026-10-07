"""Contrato HTTP: schemas Pydantic de entrada e de saída.

Nomes e estruturas pensados para a tela (cliente HTTP), não para o banco.
A conversão de EnxovalCompleto → EnxovalSaida vive em
``servicos/apresentacao.py``, que tem acesso ao contexto de domínio necessário.
"""
import uuid
from datetime import date

from pydantic import BaseModel, Field

from app.db.enums import Faixa, MomentoCompra, Moradia, PerfilCodigo, Prioridade, Tamanho, TemaSeguranca
from app.servicos.escrita import DadosRespostas


# ---------------------------------------------------------------------------
# Utilitários de erro
# ---------------------------------------------------------------------------


class Erro(BaseModel):
    """Resposta de erro padrão da API.

    Attributes:
        erro: Código de erro em snake_case (ex.: ``enxoval_nao_encontrado``).
        mensagem: Mensagem legível em português para exibição na tela.
    """

    erro: str
    mensagem: str


# ---------------------------------------------------------------------------
# Schemas de entrada
# ---------------------------------------------------------------------------


class RespostasEntrada(BaseModel):
    """Respostas do questionário enviadas pelo cliente para criar ou editar um enxoval."""

    municipio_codigo: int = Field(gt=0, description="Código IBGE do município.")
    data_prevista: date = Field(description="Data prevista de nascimento (AAAA-MM-DD).")
    dias_entre_lavagens: int = Field(ge=1, le=7, description="Frequência de lavagem de roupas.")
    moradia: Moradia = Field(description="Tipo de moradia da família.")
    tem_carro: bool = Field(description="A família tem carro próprio.")
    orcamento: Faixa = Field(description="Faixa de orçamento para compras.")
    primeiro_filho: bool = Field(description="É o primeiro filho da família.")
    correcao_perfil: PerfilCodigo | None = Field(
        default=None,
        description="Correção manual do perfil de clima (sobrescreve o padrão da cidade).",
    )

    def para_servico(self) -> DadosRespostas:
        """Converte para o dataclass de entrada dos serviços de domínio."""
        return DadosRespostas(**self.model_dump())


class MarcacaoEntrada(BaseModel):
    """Quantidades marcadas pela família para uma linha da planilha."""

    comprada: int = Field(ge=0, description="Unidades compradas pela família.")
    ganhada: int = Field(ge=0, description="Unidades ganhas (chá de bebê, etc.).")
    ja_tinha: int = Field(ge=0, description="Unidades que já existiam em casa.")


class CompletarEntrada(BaseModel):
    """Origem para completar o que falta em uma linha (marcar tudo)."""

    origem: str = Field(
        pattern="^(comprada|ganhada|ja_tinha)$",
        description="Como contabilizar o restante: 'comprada', 'ganhada' ou 'ja_tinha'.",
    )


# ---------------------------------------------------------------------------
# Schemas de saída — partes reutilizáveis
# ---------------------------------------------------------------------------


class MunicipioSaida(BaseModel):
    """Dados do município do enxoval."""

    codigo_ibge: int
    nome: str
    uf: str


class PerfilSaida(BaseModel):
    """Perfil de clima com suas características sazonais."""

    codigo: PerfilCodigo
    nome: str
    descricao: str
    meses_frios: list[int]
    meses_frescos: list[int]


class RespostasSaida(BaseModel):
    """Respostas do questionário persistidas, enriquecidas com dados do município."""

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
    """Categoria de itens do catálogo (ex.: Roupas, Higiene)."""

    slug: str
    nome: str
    ordem: int


class LinhaSaida(BaseModel):
    """Uma linha da planilha: item calculado pelo motor mesclado com as marcações da família."""

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
    momento_compra: MomentoCompra


class LinhaForaSaida(BaseModel):
    """Linha marcada pela família que não está mais na lista calculada atual."""

    chave: str
    comprada: int
    ganhada: int
    ja_tinha: int


class MarcasSaida(BaseModel):
    """Marcas sugeridas para um item, já filtradas pelo orçamento da família."""

    nomes: list[str]
    faixa: Faixa | None
    faixa_aproximada: bool


class FichaSaida(BaseModel):
    """Ficha informativa de um item: o que é, como escolher, marcas e alertas."""

    slug: str
    nome: str
    para_que_serve: str
    como_escolher: str
    idade_inicio_meses: int
    marcas: MarcasSaida
    dicas: list[str]
    regras_seguranca: list[str]


class FaseSaida(BaseModel):
    """Uma fase do roteiro de compras com datas calculadas a partir da data prevista."""

    codigo: str
    nome: str
    texto: str
    inicio: date
    fim: date
    atual: bool


class AlertaSaida(BaseModel):
    """Alerta de segurança com a data a partir da qual passa a ser relevante."""

    codigo: str
    tema: TemaSeguranca
    texto: str
    base: str
    ativo_a_partir: date
    ativo_ate: date
    itens: list[str]


class ResumoSaida(BaseModel):
    """Resumo quantitativo da planilha."""

    dias_sem_lavar: int
    total_unidades: int
    aviso_volume_alto: bool
    destacar_ja_tinha: bool


class ProgressoSaida(BaseModel):
    """Progresso de compras da família em relação ao total calculado."""

    total_unidades: int
    atendidas: int
    faltam: int
    percentual: int


# ---------------------------------------------------------------------------
# Schema raiz de saída
# ---------------------------------------------------------------------------


class EnxovalSaida(BaseModel):
    """Enxoval completo: respostas, lista calculada, roteiro, fichas e progresso."""

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
    """Resposta de criação de enxoval: apenas o UUID gerado."""

    id: uuid.UUID
