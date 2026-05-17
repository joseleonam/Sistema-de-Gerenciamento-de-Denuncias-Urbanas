"""
Router de Localizações.
Gerencia endereços e coordenadas geográficas das denúncias.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from app.core.database import get_session
from app.models import (
    Localizacao,
    LocalizacaoCreate,
    LocalizacaoRead,
    LocalizacaoUpdate,
)

router = APIRouter(prefix="/localizacoes", tags=["Localizações"])


@router.post("/", response_model=LocalizacaoRead, status_code=status.HTTP_201_CREATED)
async def criar_localizacao(
    loc_in: LocalizacaoCreate,
    session: AsyncSession = Depends(get_session),
) -> Localizacao:
    """Cria um novo registro de localização."""
    loc = Localizacao.model_validate(loc_in)
    session.add(loc)
    await session.flush()
    await session.refresh(loc)
    return loc


@router.get("/", response_model=Page[LocalizacaoRead])
async def listar_localizacoes(
    bairro: str | None = Query(default=None, description="Filtrar por bairro (parcial)"),
    cidade: str | None = Query(default=None, description="Filtrar por cidade"),
    estado: str | None = Query(default=None, description="Filtrar por UF"),
    session: AsyncSession = Depends(get_session),
) -> Page[LocalizacaoRead]:
    """Lista localizações com paginação e filtros opcionais."""
    query = select(Localizacao)
    if bairro:
        query = query.where(Localizacao.bairro.ilike(f"%{bairro}%"))
    if cidade:
        query = query.where(Localizacao.cidade.ilike(f"%{cidade}%"))
    if estado:
        query = query.where(Localizacao.estado == estado.upper())
    query = query.order_by(Localizacao.cidade, Localizacao.bairro)
    return await paginate(session, query)


@router.get("/{localizacao_id}", response_model=LocalizacaoRead)
async def obter_localizacao(
    localizacao_id: int,
    session: AsyncSession = Depends(get_session),
) -> Localizacao:
    """Retorna uma localização pelo ID."""
    result = await session.execute(select(Localizacao).where(Localizacao.id == localizacao_id))
    loc = result.scalar_one_or_none()
    if not loc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Localização não encontrada.")
    return loc


@router.patch("/{localizacao_id}", response_model=LocalizacaoRead)
async def atualizar_localizacao(
    localizacao_id: int,
    loc_in: LocalizacaoUpdate,
    session: AsyncSession = Depends(get_session),
) -> Localizacao:
    """Atualiza uma localização existente."""
    result = await session.execute(select(Localizacao).where(Localizacao.id == localizacao_id))
    loc = result.scalar_one_or_none()
    if not loc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Localização não encontrada.")
    data = loc_in.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(loc, key, value)
    session.add(loc)
    await session.flush()
    await session.refresh(loc)
    return loc


@router.delete("/{localizacao_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_localizacao(
    localizacao_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Remove uma localização pelo ID."""
    result = await session.execute(select(Localizacao).where(Localizacao.id == localizacao_id))
    loc = result.scalar_one_or_none()
    if not loc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Localização não encontrada.")
    await session.delete(loc)
