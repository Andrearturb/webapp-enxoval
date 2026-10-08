import logging

from fastapi import APIRouter, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy import create_engine
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.admin import montar_admin
from app.config import Configuracoes, obter_configuracoes
from app.erros import ErroDominio
from app.log import instalar_redator_de_uuid
from app.rotas import saude

logger = logging.getLogger(__name__)


def criar_app(cfg: Configuracoes | None = None) -> FastAPI:
    instalar_redator_de_uuid()
    cfg = cfg or obter_configuracoes()
    app = FastAPI(
        title="Enxoval Inteligente",
        docs_url="/api/docs" if cfg.docs_habilitado else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if cfg.docs_habilitado else None,
    )
    api = APIRouter(prefix="/api/v1")
    api.include_router(saude.router)

    from app.rotas import catalogo as rotas_catalogo
    from app.rotas import enxovais as rotas_enxovais
    from app.rotas import exportar as rotas_exportar
    from app.rotas import linhas as rotas_linhas

    api.include_router(rotas_catalogo.router)
    api.include_router(rotas_enxovais.router)
    api.include_router(rotas_linhas.router)
    api.include_router(rotas_exportar.router)

    app.include_router(api)
    if cfg.admin_habilitado:
        montar_admin(app, create_engine(cfg.database_url, pool_pre_ping=True))

    @app.exception_handler(ErroDominio)
    async def _erro_de_dominio(request: Request, erro: ErroDominio) -> JSONResponse:
        return JSONResponse(
            status_code=erro.status,
            content={"erro": erro.codigo, "mensagem": erro.mensagem},
        )

    @app.exception_handler(StarletteHTTPException)
    async def _erro_http(request: Request, erro: StarletteHTTPException) -> JSONResponse:
        """Converte 404/405 e outros erros HTTP do Starlette para o formato padrão.

        Sem este handler, rotas desconhecidas retornam ``{"detail": "Not Found"}``
        (formato interno do Starlette/FastAPI), fora do contrato ``{erro, mensagem}``.
        """
        _codigos: dict[int, tuple[str, str]] = {
            404: ("nao_encontrado", "Este endereço não existe."),
            405: ("metodo_nao_permitido", "Método HTTP não permitido neste endereço."),
        }
        codigo, mensagem = _codigos.get(
            erro.status_code,
            ("erro_http", "Erro na requisição HTTP."),
        )
        conteudo = erro.detail if isinstance(erro.detail, dict) else {"erro": codigo, "mensagem": mensagem}
        return JSONResponse(
            status_code=erro.status_code,
            content=conteudo,
            headers=erro.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def _erro_de_validacao(
        request: Request, erro: RequestValidationError
    ) -> JSONResponse:
        # data_prevista malformada (29/30 de fevereiro, texto, formato errado) tem
        # mensagem própria dizendo o que é aceito; os outros campos usam a genérica.
        if any("data_prevista" in e["loc"] for e in erro.errors()):
            return JSONResponse(
                status_code=422,
                content={
                    "erro": "data_prevista_invalida",
                    "mensagem": (
                        "Informe uma data válida no formato AAAA-MM-DD, entre um ano "
                        "atrás e 10 meses à frente de hoje."
                    ),
                },
            )
        return JSONResponse(
            status_code=422,
            content={
                "erro": "dados_invalidos",
                "mensagem": "Confira os dados enviados: algum campo está faltando ou fora do formato.",
            },
        )

    @app.exception_handler(Exception)
    async def _erro_inesperado(request: Request, erro: Exception) -> JSONResponse:
        # Template da rota (ex.: "/enxovais/{enxoval_id}"), nunca o caminho com o
        # UUID real; a fábrica de log (app.log) cobre o que ainda escapar (ex.: a pilha).
        rota = request.scope.get("route")
        caminho = rota.path if rota is not None else "?"
        logger.exception("erro inesperado em %s", caminho)
        return JSONResponse(
            status_code=500,
            content={
                "erro": "erro_interno",
                "mensagem": "Algo deu errado do nosso lado. Tente de novo em instantes.",
            },
        )

    @app.middleware("http")
    async def _cabecalhos_de_privacidade(request: Request, proximo):
        resposta = await proximo(request)
        if request.url.path.startswith("/api/v1/enxovais"):
            resposta.headers["Referrer-Policy"] = "no-referrer"
            resposta.headers["X-Robots-Tag"] = "noindex"
        return resposta

    return app


app = criar_app()
