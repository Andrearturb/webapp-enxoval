from enum import StrEnum


class Prioridade(StrEnum):
    ESSENCIAL = "essencial"
    UTIL = "util"
    PODE_ESPERAR = "pode_esperar"


class UsoClima(StrEnum):
    NEUTRO = "neutro"
    DIVIDE = "divide"
    SO_FRIO = "so_frio"


class Tamanho(StrEnum):
    RN = "RN"
    P = "P"
    M = "M"
    G = "G"
    GG = "GG"


class Condicao(StrEnum):
    COM_CARRO = "com_carro"
    SEM_CARRO = "sem_carro"
    APARTAMENTO = "apartamento"
    CASA_SEM_ESCADA = "casa_sem_escada"
    CASA_COM_ESCADA = "casa_com_escada"
    PERFIL_QUENTE = "perfil_quente"
    PERFIL_MODERADO = "perfil_moderado"
    PERFIL_FRIO = "perfil_frio"


class Efeito(StrEnum):
    INCLUIR_SO_SE = "incluir_so_se"
    MUDAR_PRIORIDADE = "mudar_prioridade"
    DICA = "dica"


class Faixa(StrEnum):
    ECONOMICO = "economico"
    INTERMEDIARIO = "intermediario"
    INVESTIR = "investir"


class PerfilCodigo(StrEnum):
    QUENTE = "quente"
    MODERADO = "moderado"
    FRIO = "frio"


class ReferenciaFase(StrEnum):
    GESTACAO_SEMANA = "gestacao_semana"
    BEBE_MES = "bebe_mes"


class TemaSeguranca(StrEnum):
    SONO = "sono"
    TRANSPORTE = "transporte"
    BANHO = "banho"
    ALIMENTACAO = "alimentacao"
    CASA = "casa"
    BRINQUEDOS = "brinquedos"
    GERAL = "geral"


class Moradia(StrEnum):
    APARTAMENTO = "apartamento"
    CASA_SEM_ESCADA = "casa_sem_escada"
    CASA_COM_ESCADA = "casa_com_escada"


class MomentoCompra(StrEnum):
    ATRASADO = "atrasado"
    AGORA = "agora"
    PROXIMA_FASE = "proxima_fase"
    FUTURO = "futuro"
