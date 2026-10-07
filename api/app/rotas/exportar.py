"""Endpoints de exportação da planilha (PDF, XLSX, CSV)."""
import uuid
from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.acesso import verificar_acesso
from app.db.sessao import obter_sessao
from app.dependencias import obter_hoje
from app.exportar.csv_ import gerar_csv
from app.exportar.pdf import gerar_pdf
from app.exportar.xlsx import gerar_xlsx
from app.rotas.schemas import Erro, montar_saida
from app.servicos.leitura import ler_enxoval

router = APIRouter(
    prefix="/enxovais",
    tags=["enxoval"],
    responses={404: {"model": Erro}},
    dependencies=[Depends(verificar_acesso)],
)


def _nome_arquivo(enxoval_id: uuid.UUID, extensao: str) -> str:
    return f"enxoval-{enxoval_id}.{extensao}"


@router.get("/{enxoval_id}/exportar.csv")
def exportar_csv(
    enxoval_id: uuid.UUID,
    sessao: Session = Depends(obter_sessao),
    hoje: date = Depends(obter_hoje),
) -> Response:
    saida = montar_saida(ler_enxoval(sessao, enxoval_id, hoje))
    conteudo = gerar_csv(saida).encode("utf-8-sig")
    return Response(
        content=conteudo,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": f'attachment; filename="{_nome_arquivo(enxoval_id, "csv")}"',
        },
    )


@router.get("/{enxoval_id}/exportar.xlsx")
def exportar_xlsx(
    enxoval_id: uuid.UUID,
    sessao: Session = Depends(obter_sessao),
    hoje: date = Depends(obter_hoje),
) -> Response:
    saida = montar_saida(ler_enxoval(sessao, enxoval_id, hoje))
    conteudo = gerar_xlsx(saida)
    return Response(
        content=conteudo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="{_nome_arquivo(enxoval_id, "xlsx")}"',
        },
    )


@router.get("/{enxoval_id}/exportar.pdf")
def exportar_pdf(
    enxoval_id: uuid.UUID,
    sessao: Session = Depends(obter_sessao),
    hoje: date = Depends(obter_hoje),
) -> Response:
    saida = montar_saida(ler_enxoval(sessao, enxoval_id, hoje))
    conteudo = gerar_pdf(saida, hoje)
    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{_nome_arquivo(enxoval_id, "pdf")}"',
        },
    )
