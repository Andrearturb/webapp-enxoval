from fastapi import APIRouter, FastAPI
from sqlalchemy import create_engine

from app.admin import montar_admin
from app.config import Configuracoes, obter_configuracoes
from app.rotas import saude


def criar_app(cfg: Configuracoes | None = None) -> FastAPI:
    cfg = cfg or obter_configuracoes()
    app = FastAPI(
        title="Enxoval Inteligente",
        docs_url="/api/docs" if cfg.docs_habilitado else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if cfg.docs_habilitado else None,
    )
    api = APIRouter(prefix="/api/v1")
    api.include_router(saude.router)
    app.include_router(api)
    if cfg.admin_habilitado:
        montar_admin(app, create_engine(cfg.database_url, pool_pre_ping=True))
    return app


app = criar_app()
