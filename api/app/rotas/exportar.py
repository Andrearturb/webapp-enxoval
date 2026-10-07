"""Endpoints de exportação da planilha: CSV, XLSX e PDF.

Cada endpoint lê o enxoval via ``EnxovalService``, monta o schema de saída
e delega a geração do arquivo para o módulo de exportação correspondente.
"""
import uuid
from datetime import date

from fastapi import APIRouter, Depends
from fastapi.responses import Response

from app.acesso import verificar_acesso
from app.dependencias import obter_hoje, obter_servico
from app.exportar.csv_ import gerar_csv
from app.exportar.pdf import gerar_pdf
from app.exportar.xlsx import gerar_xlsx
from app.rotas.schemas import Erro
from app.servicos.apresentacao import montar_saida
from app.servicos.enxoval_service import EnxovalService

router = APIRouter(
    prefix="/enxovais",
    tags=["enxoval"],
    responses={404: {"model": Erro}},
    dependencies=[Depends(verificar_acesso)],
)


def _nome_arquivo(enxoval_id: uuid.UUID, extensao: str) -> str:
    """Gera o nome de arquivo para o cabeçalho Content-Disposition."""
    return f"enxoval-{enxoval_id}.{extensao}"


@router.get("/{enxoval_id}/exportar.csv")
def exportar_csv(
    enxoval_id: uuid.UUID,
    servico: EnxovalService = Depends(obter_servico),
) -> Response:
    """Exporta a planilha em CSV com BOM UTF-8 para compatibilidade com Excel."""
    saida = montar_saida(servico.ler(enxoval_id))
    conteudo = gerar_csv(saida).encode("utf-8-sig")
    return Response(
        content=conteudo,
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{_nome_arquivo(enxoval_id, "csv")}"'},
    )


@router.get("/{enxoval_id}/exportar.xlsx")
def exportar_xlsx(
    enxoval_id: uuid.UUID,
    servico: EnxovalService = Depends(obter_servico),
) -> Response:
    """Exporta a planilha em XLSX com abas Planilha e Roteiro."""
    saida = montar_saida(servico.ler(enxoval_id))
    conteudo = gerar_xlsx(saida)
    return Response(
        content=conteudo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{_nome_arquivo(enxoval_id, "xlsx")}"'},
    )


@router.get("/{enxoval_id}/exportar.pdf")
def exportar_pdf(
    enxoval_id: uuid.UUID,
    hoje: date = Depends(obter_hoje),
    servico: EnxovalService = Depends(obter_servico),
) -> Response:
    """Exporta a planilha em PDF via WeasyPrint com template HTML."""
    saida = montar_saida(servico.ler(enxoval_id))
    conteudo = gerar_pdf(saida, hoje)
    return Response(
        content=conteudo,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{_nome_arquivo(enxoval_id, "pdf")}"'},
    )
