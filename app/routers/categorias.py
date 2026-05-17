"""
Router de Categorias.
Gerencia os tipos de problemas urbanos (buraco, iluminação, lixo, etc.).
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import func, select

from app.core.database import get_session
from app.models import (
    Categoria,
    CategoriaCreate,
    CategoriaRead,
    CategoriaUpdate,
    Denuncia,
    DenunciaCategoria,
    DenunciaRead,
)

router = APIRouter(prefix="/categorias", tags=["Categorias"])


@router.post("/", response_model=CategoriaRead, status_code=status.HTTP_201_CREATED)
async def criar_categoria(
    categoria_in: CategoriaCreate,
    session: AsyncSession = Depends(get_session),
) -> Categoria:
    """Cria uma nova categoria de problema urbano."""
    existing = await session.execute(
        select(Categoria).where(Categoria.nome == categoria_in.nome)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Categoria com esse nome já existe.",
        )
    categoria = Categoria.model_validate(categoria_in)
    session.add(categoria)
    await session.flush()
    await session.refresh(categoria)
    return categoria


@router.get("/", response_model=Page[CategoriaRead])
async def listar_categorias(
    ativa: bool | None = Query(default=None),
    nome: str | None = Query(default=None, description="Busca parcial por nome"),
    session: AsyncSession = Depends(get_session),
) -> Page[CategoriaRead]:
    """Lista categorias com paginação e filtros opcionais."""
    query = select(Categoria)
    if ativa is not None:
        query = query.where(Categoria.ativa == ativa)
    if nome:
        query = query.where(Categoria.nome.ilike(f"%{nome}%"))
    query = query.order_by(Categoria.nome)
    return await paginate(session, query)


@router.get("/{categoria_id}", response_model=CategoriaRead)
async def obter_categoria(
    categoria_id: int,
    session: AsyncSession = Depends(get_session),
) -> Categoria:
    """Retorna uma categoria pelo ID."""
    result = await session.execute(select(Categoria).where(Categoria.id == categoria_id))
    categoria = result.scalar_one_or_none()
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
    return categoria


@router.patch("/{categoria_id}", response_model=CategoriaRead)
async def atualizar_categoria(
    categoria_id: int,
    categoria_in: CategoriaUpdate,
    session: AsyncSession = Depends(get_session),
) -> Categoria:
    """Atualiza uma categoria existente."""
    result = await session.execute(select(Categoria).where(Categoria.id == categoria_id))
    categoria = result.scalar_one_or_none()
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
    data = categoria_in.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(categoria, key, value)
    session.add(categoria)
    await session.flush()
    await session.refresh(categoria)
    return categoria


@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_categoria(
    categoria_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Remove uma categoria pelo ID."""
    result = await session.execute(select(Categoria).where(Categoria.id == categoria_id))
    categoria = result.scalar_one_or_none()
    if not categoria:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
    await session.delete(categoria)


@router.get("/{categoria_id}/denuncias", response_model=Page[DenunciaRead])
async def listar_denuncias_da_categoria(
    categoria_id: int,
    session: AsyncSession = Depends(get_session),
) -> Page[DenunciaRead]:
    """Lista todas as denúncias de uma categoria específica."""
    result = await session.execute(select(Categoria).where(Categoria.id == categoria_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
    query = (
        select(Denuncia)
        .join(DenunciaCategoria, DenunciaCategoria.denuncia_id == Denuncia.id)
        .where(DenunciaCategoria.categoria_id == categoria_id)
        .order_by(Denuncia.created_at.desc())
    )
    return await paginate(session, query)


@router.get("/{categoria_id}/contagem-denuncias")
async def contar_denuncias_por_categoria(
    categoria_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Conta quantas denúncias existem para uma categoria."""
    result = await session.execute(select(Categoria).where(Categoria.id == categoria_id))
    cat = result.scalar_one_or_none()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Categoria não encontrada.")
    count_result = await session.execute(
        select(func.count())
        .select_from(DenunciaCategoria)
        .where(DenunciaCategoria.categoria_id == categoria_id)
    )
    total = count_result.scalar_one()
    return {"categoria_id": categoria_id, "nome": cat.nome, "total_denuncias": total}
