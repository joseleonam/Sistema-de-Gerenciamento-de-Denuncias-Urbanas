"""
Router de Documentos.
Gerencia upload, download e metadados de arquivos (imagens/PDFs) associados a denúncias.
"""

import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.config import get_settings
from app.core.database import get_session
from app.models import Denuncia, Document, DocumentRead

router = APIRouter(tags=["Documentos"])
settings = get_settings()


def _get_file_path(document_id: int, extension: str) -> Path:
    """Retorna o caminho físico de um arquivo pelo ID e extensão."""
    return settings.upload_path / f"{document_id}.{extension}"


def _validate_file(file: UploadFile) -> tuple[str, str]:
    """
    Valida tipo MIME e extensão do arquivo enviado.
    Retorna (content_type, extension).
    """
    allowed_mime = {
        "image/jpeg": "jpg",
        "image/png": "png",
        "image/gif": "gif",
        "application/pdf": "pdf",
    }
    content_type = file.content_type or ""
    extension = allowed_mime.get(content_type)
    if not extension:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Tipo de arquivo não permitido: {content_type}. Permitidos: JPEG, PNG, GIF, PDF.",
        )
    return content_type, extension


# ─────────────────────────────────────────────
# Endpoints específicos de denúncia
# ─────────────────────────────────────────────

@router.post(
    "/denuncias/{denuncia_id}/documents",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Documentos"],
    summary="Envia um novo documento para uma denúncia",
)
async def upload_documento(
    denuncia_id: int,
    file: UploadFile = File(..., description="Arquivo de imagem (JPEG/PNG/GIF) ou PDF"),
    session: AsyncSession = Depends(get_session),
) -> Document:
    """Faz upload de um arquivo e salva os metadados no banco."""
    # Valida denúncia
    denuncia = await session.get(Denuncia, denuncia_id)
    if not denuncia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Denúncia não encontrada.")

    content_type, extension = _validate_file(file)

    # Lê o conteúdo para verificar tamanho
    contents = await file.read()
    size_bytes = len(contents)
    if size_bytes > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Arquivo muito grande. Máximo permitido: {settings.MAX_FILE_SIZE_MB}MB.",
        )

    # Cria o metadado no banco primeiro para obter o ID
    doc = Document(
        original_filename=file.filename or "arquivo",
        content_type=content_type,
        extension=extension,
        size_bytes=size_bytes,
        denuncia_id=denuncia_id,
    )
    session.add(doc)
    await session.flush()
    await session.refresh(doc)

    # Salva o arquivo usando o ID como nome
    file_path = _get_file_path(doc.id, extension)
    file_path.write_bytes(contents)

    return doc


@router.get(
    "/denuncias/{denuncia_id}/documents",
    response_model=Page[DocumentRead],
    tags=["Documentos"],
    summary="Lista os documentos de uma denúncia",
)
async def listar_documentos_denuncia(
    denuncia_id: int,
    session: AsyncSession = Depends(get_session),
) -> Page[DocumentRead]:
    """Lista todos os documentos associados a uma denúncia."""
    denuncia = await session.get(Denuncia, denuncia_id)
    if not denuncia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Denúncia não encontrada.")
    query = (
        select(Document)
        .where(Document.denuncia_id == denuncia_id)
        .order_by(Document.created_at.desc())
    )
    return await paginate(session, query)


# ─────────────────────────────────────────────
# Endpoints genéricos de documento
# ─────────────────────────────────────────────

@router.get(
    "/documents/{document_id}",
    response_model=DocumentRead,
    tags=["Documentos"],
    summary="Retorna os metadados de um documento",
)
async def obter_documento(
    document_id: int,
    session: AsyncSession = Depends(get_session),
) -> Document:
    """Retorna os metadados de um documento pelo ID."""
    doc = await session.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado.")
    return doc


@router.get(
    "/documents/{document_id}/download",
    tags=["Documentos"],
    summary="Baixa ou exibe o arquivo de um documento",
)
async def download_documento(
    document_id: int,
    session: AsyncSession = Depends(get_session),
) -> FileResponse:
    """Retorna o arquivo físico associado a um documento."""
    doc = await session.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado.")

    file_path = _get_file_path(doc.id, doc.extension)
    if not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo físico não encontrado no servidor.",
        )

    return FileResponse(
        path=str(file_path),
        media_type=doc.content_type,
        filename=doc.original_filename,
    )


@router.put(
    "/documents/{document_id}",
    response_model=DocumentRead,
    tags=["Documentos"],
    summary="Substitui o arquivo de um documento",
)
async def substituir_documento(
    document_id: int,
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> Document:
    """Substitui o arquivo físico e atualiza os metadados de um documento existente."""
    doc = await session.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado.")

    content_type, extension = _validate_file(file)
    contents = await file.read()
    size_bytes = len(contents)

    if size_bytes > settings.max_file_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Arquivo muito grande. Máximo: {settings.MAX_FILE_SIZE_MB}MB.",
        )

    # Remove o arquivo antigo se extensão mudou
    old_path = _get_file_path(doc.id, doc.extension)
    if old_path.exists() and doc.extension != extension:
        old_path.unlink()

    # Salva novo arquivo
    new_path = _get_file_path(doc.id, extension)
    new_path.write_bytes(contents)

    # Atualiza metadados
    from datetime import datetime
    doc.original_filename = file.filename or doc.original_filename
    doc.content_type = content_type
    doc.extension = extension
    doc.size_bytes = size_bytes
    doc.created_at = datetime.utcnow()

    session.add(doc)
    await session.flush()
    await session.refresh(doc)
    return doc


@router.delete(
    "/documents/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Documentos"],
    summary="Remove um documento e seu arquivo físico",
)
async def remover_documento(
    document_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Remove o metadado do banco e exclui o arquivo físico do servidor."""
    doc = await session.get(Document, document_id)
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Documento não encontrado.")

    # Remove o arquivo físico
    file_path = _get_file_path(doc.id, doc.extension)
    if file_path.exists():
        file_path.unlink()

    await session.delete(doc)
