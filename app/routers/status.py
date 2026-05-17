"""
Router de Status.
Gerencia os estados das denúncias (aberto, em análise, resolvido, etc.).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import func, select

from app.core.database import get_session
from app.models import (
    SituacaoEnum,
    Status,
    StatusCreate,
    StatusRead,
    StatusUpdate,
)

router = APIRouter(prefix="/status", tags=["Status"])


@router.post("/", response_model=StatusRead, status_code=status.HTTP_201_CREATED)
async def criar_status(
    status_in: StatusCreate,
    session: AsyncSession = Depends(get_session),
) -> Status:
    """Cria um novo registro de status."""
    st = Status.model_validate(status_in)
    session.add(st)
    await session.flush()
    await session.refresh(st)
    return st


@router.get("/", response_model=Page[StatusRead])
async def listar_status(
    situacao: SituacaoEnum | None = Query(default=None, description="Filtrar por situação"),
    session: AsyncSession = Depends(get_session),
) -> Page[StatusRead]:
    """Lista registros de status com paginação."""
    query = select(Status)
    if situacao:
        query = query.where(Status.situacao == situacao)
    query = query.order_by(Status.updated_at.desc())
    return await paginate(session, query)


@router.get("/contagem-por-situacao")
async def contar_por_situacao(
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """Agrega a quantidade de denúncias por situação."""
    from app.models import Denuncia
    result = await session.execute(
        select(Status.situacao, func.count(Denuncia.id).label("total"))
        .join(Denuncia, Denuncia.status_id == Status.id)
        .group_by(Status.situacao)
        .order_by(Status.situacao)
    )
    return [{"situacao": row.situacao, "total": row.total} for row in result.all()]


@router.get("/{status_id}", response_model=StatusRead)
async def obter_status(
    status_id: int,
    session: AsyncSession = Depends(get_session),
) -> Status:
    """Retorna um status pelo ID."""
    result = await session.execute(select(Status).where(Status.id == status_id))
    st = result.scalar_one_or_none()
    if not st:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status não encontrado.")
    return st


@router.patch("/{status_id}", response_model=StatusRead)
async def atualizar_status(
    status_id: int,
    status_in: StatusUpdate,
    session: AsyncSession = Depends(get_session),
) -> Status:
    """Atualiza um status existente."""
    from datetime import datetime
    result = await session.execute(select(Status).where(Status.id == status_id))
    st = result.scalar_one_or_none()
    if not st:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status não encontrado.")
    data = status_in.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(st, key, value)
    st.updated_at = datetime.utcnow()
    session.add(st)
    await session.flush()
    await session.refresh(st)
    return st


@router.delete("/{status_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_status(
    status_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Remove um status pelo ID."""
    result = await session.execute(select(Status).where(Status.id == status_id))
    st = result.scalar_one_or_none()
    if not st:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Status não encontrado.")
    await session.delete(st)
