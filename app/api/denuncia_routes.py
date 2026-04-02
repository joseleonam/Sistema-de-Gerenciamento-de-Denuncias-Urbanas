from datetime import datetime
from io import StringIO
import csv
import zipfile
from typing import Generator

from fastapi import APIRouter, HTTPException, Query, Response, status
from fastapi.responses import StreamingResponse

from app.persistence.denuncia_repository import DenunciaRepository
from app.models.denuncia import DenunciaCreate, DenunciaUpdate, DenunciaOut

router = APIRouter()
repo = DenunciaRepository(table_path="data/denuncias", seq_file="data/denuncias.seq")


@router.post("/", response_model=DenunciaOut, status_code=status.HTTP_201_CREATED)
def create_denuncia(denuncia: DenunciaCreate):
    nova = repo.insert_denuncia(denuncia)
    return DenunciaOut(**nova.model_dump())


@router.get("/", response_model=list[DenunciaOut])
def list_denuncias(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=500)):
    return [DenunciaOut(**item.model_dump()) for item in repo.list_denuncias(page=page, page_size=page_size)]


@router.get("/{id}", response_model=DenunciaOut)
def get_denuncia(id: int):
    result = repo.get_denuncia(id)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Denúncia não encontrada")
    return DenunciaOut(**result.model_dump())


@router.put("/{id}", response_model=DenunciaOut)
def update_denuncia(id: int, payload: DenunciaUpdate):
    result = repo.update_denuncia(id, payload)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Denúncia não encontrada")
    return DenunciaOut(**result.model_dump())


@router.patch("/{id}", response_model=DenunciaOut)
def patch_denuncia(id: int, payload: DenunciaUpdate):
    result = repo.update_denuncia(id, payload)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Denúncia não encontrada")
    return DenunciaOut(**result.model_dump())


@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_denuncia(id: int):
    deleted = repo.delete_denuncia(id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Denúncia não encontrada")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/count")
def count_denuncias():
    return {"count": repo.count_denuncias()}


def _generate_csv_rows(batch_size: int = 1000) -> Generator[str, None, None]:
    table = repo._table()
    first_line = True
    for batch in table.to_pyarrow_table().to_batches(batch_size=batch_size):
        df = batch.to_pandas()
        if df.empty:
            continue
        if first_line:
            yield ",".join(df.columns) + "\n"
            first_line = False
        csv_buffer = StringIO()
        writer = csv.writer(csv_buffer)
        for row in df.itertuples(index=False):
            values = ["" if v is None else v.isoformat() if hasattr(v, "isoformat") else v for v in row]
            writer.writerow(values)
        yield csv_buffer.getvalue()


@router.get("/export.csv")
def export_csv():
    return StreamingResponse(_generate_csv_rows(), media_type="text/csv", headers={"Content-Disposition": "attachment; filename=denuncias.csv"})


@router.get("/export.zip")
def export_zip():
    def stream_zip() -> Generator[bytes, None, None]:
        with StringIO() as csv_buffer:
            # nao carrega tudo na memória fixo: processa em blocos
            csv_buffer.write("")
            # Cria arquivo zip em memória por pedaços
            with zipfile.ZipFile(csv_buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
                # Criar nome interno e escrever conteúdo em pedaços
                # Para não materializar tudo, gravamos em bytes temporários
                inner = StringIO()
                for chunk in _generate_csv_rows():
                    inner.write(chunk)
                zf.writestr("denuncias.csv", inner.getvalue())
            yield csv_buffer.getvalue().encode("utf-8")

    return StreamingResponse(stream_zip(), media_type="application/zip", headers={"Content-Disposition": "attachment; filename=denuncias.zip"})
