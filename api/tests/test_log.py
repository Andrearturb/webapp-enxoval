import logging
import sys

from app.log import PADRAO_UUID, instalar_redator_de_uuid, redigir_registro

UUID_EXEMPLO = "c7ef724d-b37f-4db1-90bf-54fb675a84f7"


def _registro(msg, args=(), exc_info=None) -> logging.LogRecord:
    return logging.LogRecord(
        name="teste", level=logging.ERROR, pathname=__file__, lineno=1,
        msg=msg, args=args, exc_info=exc_info,
    )


def test_redige_uuid_na_mensagem():
    registro = redigir_registro(_registro(f"GET /enxovais/{UUID_EXEMPLO} 500"))

    assert UUID_EXEMPLO not in registro.getMessage()
    assert "[uuid]" in registro.getMessage()


def test_redige_uuid_nos_argumentos():
    registro = redigir_registro(_registro("rota: %s", args=(f"/enxovais/{UUID_EXEMPLO}",)))

    assert UUID_EXEMPLO not in registro.getMessage()


def test_redige_uuid_na_pilha_de_erro():
    try:
        raise RuntimeError(f"falhou para o enxoval {UUID_EXEMPLO}")
    except RuntimeError:
        registro = redigir_registro(_registro("erro inesperado", exc_info=sys.exc_info()))

    formatado = logging.Formatter().format(registro)
    assert UUID_EXEMPLO not in formatado
    assert "[uuid]" in formatado


def test_mensagem_sem_uuid_nao_e_alterada():
    registro = redigir_registro(_registro("tudo bem por aqui"))

    assert registro.getMessage() == "tudo bem por aqui"


def test_padrao_uuid_reconhece_formato_canonico():
    assert PADRAO_UUID.search(UUID_EXEMPLO)
    assert not PADRAO_UUID.search("nao-e-um-uuid")


def test_instalado_no_processo_redige_qualquer_logger(caplog):
    """Fim a fim: um logger de qualquer módulo, criado depois de instalar, sai redigido."""
    instalar_redator_de_uuid()
    logger = logging.getLogger("app._teste_log_qualquer_modulo")

    with caplog.at_level(logging.ERROR):
        logger.error("algo com %s", f"/enxovais/{UUID_EXEMPLO}")

    assert UUID_EXEMPLO not in caplog.text
    assert "[uuid]" in caplog.text


def test_instalar_e_idempotente():
    fabrica_antes = logging.getLogRecordFactory()

    instalar_redator_de_uuid()
    fabrica_depois = logging.getLogRecordFactory()

    assert fabrica_antes is fabrica_depois
