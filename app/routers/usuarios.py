"""
Router de Usuários.
Endpoints CRUD e consultas específicas para cidadãos cadastrados.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import func, select

from app.core.database import get_session
from app.models import (
    Denuncia,
    DenunciaRead,
    Usuario,
    UsuarioCreate,
    UsuarioRead,
    UsuarioReadWithDenuncias,
    UsuarioUpdate,
)

router = APIRouter(prefix="/usuarios", tags=["Usuários"])


@router.post("/", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
async def criar_usuario(
    usuario_in: UsuarioCreate,
    session: AsyncSession = Depends(get_session),
) -> Usuario:
    """Cria um novo usuário (cidadão)."""
    # Verifica duplicidade de email
    existing = await session.execute(
        select(Usuario).where(Usuario.email == usuario_in.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado.",
        )
    usuario = Usuario.model_validate(usuario_in)
    session.add(usuario)
    await session.flush()
    await session.refresh(usuario)
    return usuario


@router.get("/", response_model=Page[UsuarioRead])
async def listar_usuarios(
    ativo: bool | None = Query(default=None, description="Filtrar por usuários ativos/inativos"),
    nome: str | None = Query(default=None, description="Filtrar por nome (parcial)"),
    session: AsyncSession = Depends(get_session),
) -> Page[UsuarioRead]:
    """Lista usuários com paginação, com filtros opcionais."""
    query = select(Usuario)
    if ativo is not None:
        query = query.where(Usuario.ativo == ativo)
    if nome:
        query = query.where(Usuario.nome.ilike(f"%{nome}%"))
    query = query.order_by(Usuario.nome)
    return await paginate(session, query)


@router.get("/{usuario_id}", response_model=UsuarioReadWithDenuncias)
async def obter_usuario(
    usuario_id: int,
    session: AsyncSession = Depends(get_session),
) -> Usuario:
    """Retorna um usuário pelo ID, incluindo suas denúncias."""
    result = await session.execute(
        select(Usuario)
        .where(Usuario.id == usuario_id)
        .options(selectinload(Usuario.denuncias))
    )
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Usuário {usuario_id} não encontrado.",
        )
    return usuario


@router.patch("/{usuario_id}", response_model=UsuarioRead)
async def atualizar_usuario(
    usuario_id: int,
    usuario_in: UsuarioUpdate,
    session: AsyncSession = Depends(get_session),
) -> Usuario:
    """Atualiza campos de um usuário existente."""
    result = await session.execute(select(Usuario).where(Usuario.id == usuario_id))
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    data = usuario_in.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(usuario, key, value)
    session.add(usuario)
    await session.flush()
    await session.refresh(usuario)
    return usuario


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_usuario(
    usuario_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Remove um usuário pelo ID."""
    result = await session.execute(select(Usuario).where(Usuario.id == usuario_id))
    usuario = result.scalar_one_or_none()
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    await session.delete(usuario)


@router.get("/{usuario_id}/denuncias", response_model=Page[DenunciaRead])
async def listar_denuncias_do_usuario(
    usuario_id: int,
    session: AsyncSession = Depends(get_session),
) -> Page[DenunciaRead]:
    """Lista todas as denúncias feitas por um usuário específico."""
    result = await session.execute(select(Usuario).where(Usuario.id == usuario_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    query = select(Denuncia).where(Denuncia.usuario_id == usuario_id).order_by(Denuncia.created_at.desc())
    return await paginate(session, query)


@router.get("/{usuario_id}/contagem-denuncias")
async def contar_denuncias_do_usuario(
    usuario_id: int,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Conta o total de denúncias de um usuário."""
    result = await session.execute(select(Usuario).where(Usuario.id == usuario_id))
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")
    count_result = await session.execute(
        select(func.count()).where(Denuncia.usuario_id == usuario_id)
    )
    total = count_result.scalar_one()
    return {"usuario_id": usuario_id, "total_denuncias": total}
