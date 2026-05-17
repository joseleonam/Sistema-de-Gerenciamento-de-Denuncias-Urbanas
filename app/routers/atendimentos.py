"""
Router de Atendimentos.
Gerencia os registros de resposta dos órgãos públicos às denúncias.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
from sqlmodel import func, select

from app.core.database import get_session
from app.models import (
    Atendimento,
    AtendimentoCreate,
    AtendimentoRead,
    AtendimentoUpdate,
    Denuncia,
)

router = APIRouter(prefix="/atendimentos", tags=["Atendimentos"])


@router.post("/", response_model=AtendimentoRead, status_code=status.HTTP_201_CREATED)
async def criar_atendimento(
    atendimento_in: AtendimentoCreate,
    session: AsyncSession = Depends(get_session),
) -> Atendimento:
    """Registra um novo atendimento a uma denúncia."""
    denuncia = await session.get(Denuncia, atendimento_in.denuncia_id)
    if not denuncia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Denúncia não encontrada.")
    atendimento = Atendimento.model_validate(atendimento_in)
    session.add(atendimento)
    await session.flush()
    await session.refresh(atendimento)
    return atendimento


@router.get("/", response_model=Page[AtendimentoRead])
async def listar_atendimentos(
    orgao: str | None = Query(default=None, description="Filtrar por órgão responsável (parcial)"),
    denuncia_id: int | None = Query(default=None),
    concluido: bool | None = Query(default=None, description="True = com data_conclusao; False = sem"),
    session: AsyncSession = Depends(get_session),
) -> Page[AtendimentoRead]:
    """Lista atendimentos com paginação e filtros."""
    query = select(Atendimento)
    if orgao:
        query = query.where(Atendimento.orgao_responsavel.ilike(f"%{orgao}%"))
    if denuncia_id:
        query = query.where(Atendimento.denuncia_id == denuncia_id)
    if concluido is True:
        query = query.where(Atendimento.data_conclusao.isnot(None))
    elif concluido is False:
        query = query.where(Atendimento.data_conclusao.is_(None))
    query = query.order_by(Atendimento.data_inicio.desc())
    return await paginate(session, query)


@router.get("/{atendimento_id}", response_model=AtendimentoRead)
async def obter_atendimento(
    atendimento_id: int,
    session: AsyncSession = Depends(get_session),
) -> Atendimento:
    """Retorna um atendimento pelo ID."""
    result = await session.execute(
        select(Atendimento).where(Atendimento.id == atendimento_id)
    )
    at = result.scalar_one_or_none()
    if not at:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atendimento não encontrado.")
    return at


@router.patch("/{atendimento_id}", response_model=AtendimentoRead)
async def atualizar_atendimento(
    atendimento_id: int,
    atendimento_in: AtendimentoUpdate,
    session: AsyncSession = Depends(get_session),
) -> Atendimento:
    """Atualiza um atendimento existente."""
    result = await session.execute(
        select(Atendimento).where(Atendimento.id == atendimento_id)
    )
    at = result.scalar_one_or_none()
    if not at:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atendimento não encontrado.")
    data = atendimento_in.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(at, key, value)
    session.add(at)
    await session.flush()
    await session.refresh(at)
    return at


@router.delete("/{atendimento_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_atendimento(
    atendimento_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Remove um atendimento pelo ID."""
    result = await session.execute(
        select(Atendimento).where(Atendimento.id == atendimento_id)
    )
    at = result.scalar_one_or_none()
    if not at:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Atendimento não encontrado.")
    await session.delete(at)


@router.get("/estatisticas/custo-total-por-orgao")
async def custo_por_orgao(session: AsyncSession = Depends(get_session)) -> list[dict]:
    """Retorna o custo total estimado de atendimentos agrupado por órgão."""
    result = await session.execute(
        select(
            Atendimento.orgao_responsavel,
            func.count().label("total_atendimentos"),
            func.sum(Atendimento.custo_estimado).label("custo_total"),
        )
        .where(Atendimento.custo_estimado.isnot(None))
        .group_by(Atendimento.orgao_responsavel)
        .order_by(func.sum(Atendimento.custo_estimado).desc())
    )
    return [
        {
            "orgao": row.orgao_responsavel,
            "total_atendimentos": row.total_atendimentos,
            "custo_total": round(row.custo_total or 0, 2),
        }
        for row in result.all()
    ]
