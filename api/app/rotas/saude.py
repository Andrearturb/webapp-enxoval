from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.sessao import obter_sessao

router = APIRouter(tags=["saúde"])


@router.get("/saude")
def saude(sessao: Session = Depends(obter_sessao)):
    try:
        sessao.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503, content={"status": "erro", "banco": "indisponivel"}
        )
    return {"status": "ok", "banco": "ok"}
