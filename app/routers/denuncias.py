"""
Router de Denúncias.
Entidade central do sistema. Implementa CRUD completo e diversas consultas
complexas envolvendo filtros, agregações e relacionamentos.
"""

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi_pagination import Page
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlmodel import func, select

from app.core.database import get_session
from app.models import (
    Categoria,
    Denuncia,
    DenunciaCategoria,
    DenunciaCreate,
    DenunciaRead,
    DenunciaReadFull,
    DenunciaUpdate,
    Localizacao,
    PrioridadeEnum,
    SituacaoEnum,
    Status,
    StatusCreate,
    Usuario,
)

router = APIRouter(prefix="/denuncias", tags=["Denúncias"])


async def _load_denuncia_full(denuncia_id: int, session: AsyncSession) -> Denuncia:
    """Carrega uma denúncia com todos os relacionamentos via eager loading."""
    result = await session.execute(
        select(Denuncia)
        .where(Denuncia.id == denuncia_id)
        .options(
            selectinload(Denuncia.categorias),
            selectinload(Denuncia.atendimentos),
            selectinload(Denuncia.documents),
        )
    )
    return result.scalar_one_or_none()


# ─────────────────────────────────────────────
# CRUD
# ─────────────────────────────────────────────

@router.post("/", response_model=DenunciaReadFull, status_code=status.HTTP_201_CREATED)
async def criar_denuncia(
    denuncia_in: DenunciaCreate,
    session: AsyncSession = Depends(get_session),
) -> Denuncia:
    """
    Cria uma nova denúncia urbana.
    Cria automaticamente um Status inicial como 'aberto'.
    """
    # Valida usuário
    usuario = await session.get(Usuario, denuncia_in.usuario_id)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado.")

    # Valida localização
    localizacao = await session.get(Localizacao, denuncia_in.localizacao_id)
    if not localizacao:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Localização não encontrada.")

    # Cria o status inicial
    st = Status(situacao=SituacaoEnum.aberto, descricao="Denúncia registrada pelo cidadão.")
    session.add(st)
    await session.flush()

    # Cria a denúncia
    denuncia = Denuncia(
        titulo=denuncia_in.titulo,
        descricao=denuncia_in.descricao,
        prioridade=denuncia_in.prioridade,
        usuario_id=denuncia_in.usuario_id,
        localizacao_id=denuncia_in.localizacao_id,
        status_id=st.id,
    )
    session.add(denuncia)
    await session.flush()

    # Associa categorias (many-to-many)
    for cat_id in denuncia_in.categoria_ids:
        cat = await session.get(Categoria, cat_id)
        if not cat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Categoria {cat_id} não encontrada.",
            )
        session.add(DenunciaCategoria(denuncia_id=denuncia.id, categoria_id=cat_id))

    await session.flush()
    return await _load_denuncia_full(denuncia.id, session)


@router.get("/", response_model=Page[DenunciaRead])
async def listar_denuncias(
    titulo: str | None = Query(default=None, description="Busca parcial no título"),
    prioridade: PrioridadeEnum | None = Query(default=None),
    situacao: SituacaoEnum | None = Query(default=None, description="Filtrar por situação do status"),
    categoria_id: int | None = Query(default=None),
    usuario_id: int | None = Query(default=None),
    bairro: str | None = Query(default=None),
    ano: int | None = Query(default=None, description="Filtrar por ano de criação"),
    session: AsyncSession = Depends(get_session),
) -> Page[DenunciaRead]:
    """Lista denúncias com paginação e múltiplos filtros."""
    query = select(Denuncia)

    if titulo:
        query = query.where(Denuncia.titulo.ilike(f"%{titulo}%"))
    if prioridade:
        query = query.where(Denuncia.prioridade == prioridade)
    if usuario_id:
        query = query.where(Denuncia.usuario_id == usuario_id)
    if ano:
        query = query.where(func.strftime("%Y", Denuncia.created_at) == str(ano))
    if situacao:
        query = query.join(Status, Status.id == Denuncia.status_id).where(Status.situacao == situacao)
    if categoria_id:
        query = query.join(
            DenunciaCategoria, DenunciaCategoria.denuncia_id == Denuncia.id
        ).where(DenunciaCategoria.categoria_id == categoria_id)
    if bairro:
        query = query.join(Localizacao, Localizacao.id == Denuncia.localizacao_id).where(
            Localizacao.bairro.ilike(f"%{bairro}%")
        )

    query = query.order_by(Denuncia.created_at.desc())
    return await paginate(session, query)


@router.get("/estatisticas/total")
async def total_denuncias(session: AsyncSession = Depends(get_session)) -> dict:
    """Retorna a quantidade total de denúncias cadastradas."""
    result = await session.execute(select(func.count()).select_from(Denuncia))
    return {"total_denuncias": result.scalar_one()}


@router.get("/estatisticas/por-categoria")
async def denuncias_por_categoria(session: AsyncSession = Depends(get_session)) -> list[dict]:
    """Retorna a quantidade de denúncias agrupada por categoria."""
    result = await session.execute(
        select(Categoria.nome, func.count(DenunciaCategoria.denuncia_id).label("total"))
        .join(DenunciaCategoria, DenunciaCategoria.categoria_id == Categoria.id)
        .group_by(Categoria.nome)
        .order_by(func.count(DenunciaCategoria.denuncia_id).desc())
    )
    return [{"categoria": row.nome, "total": row.total} for row in result.all()]


@router.get("/estatisticas/por-prioridade")
async def denuncias_por_prioridade(session: AsyncSession = Depends(get_session)) -> list[dict]:
    """Retorna a quantidade de denúncias por nível de prioridade."""
    result = await session.execute(
        select(Denuncia.prioridade, func.count().label("total"))
        .group_by(Denuncia.prioridade)
        .order_by(func.count().desc())
    )
    return [{"prioridade": row.prioridade, "total": row.total} for row in result.all()]


@router.get("/estatisticas/por-bairro")
async def denuncias_por_bairro(
    limite: int = Query(default=10, ge=1, le=50, description="Quantidade de bairros a retornar"),
    session: AsyncSession = Depends(get_session),
) -> list[dict]:
    """Retorna os bairros com mais denúncias registradas."""
    result = await session.execute(
        select(Localizacao.bairro, func.count(Denuncia.id).label("total"))
        .join(Denuncia, Denuncia.localizacao_id == Localizacao.id)
        .group_by(Localizacao.bairro)
        .order_by(func.count(Denuncia.id).desc())
        .limit(limite)
    )
    return [{"bairro": row.bairro, "total": row.total} for row in result.all()]


@router.get("/estatisticas/atendimentos-por-denuncia")
async def atendimentos_por_denuncia(session: AsyncSession = Depends(get_session)) -> list[dict]:
    """Retorna a quantidade de atendimentos por denúncia."""
    from app.models import Atendimento
    result = await session.execute(
        select(Denuncia.id, Denuncia.titulo, func.count(Atendimento.id).label("total_atendimentos"))
        .outerjoin(Atendimento, Atendimento.denuncia_id == Denuncia.id)
        .group_by(Denuncia.id, Denuncia.titulo)
        .order_by(func.count(Atendimento.id).desc())
        .limit(20)
    )
    return [
        {"denuncia_id": row.id, "titulo": row.titulo, "total_atendimentos": row.total_atendimentos}
        for row in result.all()
    ]


@router.get("/{denuncia_id}", response_model=DenunciaReadFull)
async def obter_denuncia(
    denuncia_id: int,
    session: AsyncSession = Depends(get_session),
) -> Denuncia:
    """Retorna uma denúncia pelo ID com todos os dados relacionados."""
    result = await session.execute(
        select(Denuncia)
        .where(Denuncia.id == denuncia_id)
        .options(
            selectinload(Denuncia.categorias),
            selectinload(Denuncia.atendimentos),
            selectinload(Denuncia.documents),
        )
    )
    denuncia = result.scalar_one_or_none()
    if not denuncia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Denúncia não encontrada.")
    return denuncia


@router.patch("/{denuncia_id}", response_model=DenunciaReadFull)
async def atualizar_denuncia(
    denuncia_id: int,
    denuncia_in: DenunciaUpdate,
    session: AsyncSession = Depends(get_session),
) -> Denuncia:
    """Atualiza dados de uma denúncia existente."""
    result = await session.execute(select(Denuncia).where(Denuncia.id == denuncia_id))
    denuncia = result.scalar_one_or_none()
    if not denuncia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Denúncia não encontrada.")

    data = denuncia_in.model_dump(exclude_unset=True, exclude={"categoria_ids"})
    for key, value in data.items():
        setattr(denuncia, key, value)
    denuncia.updated_at = datetime.utcnow()

    # Atualiza categorias se fornecidas
    if denuncia_in.categoria_ids is not None:
        # Remove associações antigas
        old_cats = await session.execute(
            select(DenunciaCategoria).where(DenunciaCategoria.denuncia_id == denuncia_id)
        )
        for dc in old_cats.scalars().all():
            await session.delete(dc)
        await session.flush()
        # Adiciona novas
        for cat_id in denuncia_in.categoria_ids:
            cat = await session.get(Categoria, cat_id)
            if not cat:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Categoria {cat_id} não encontrada.",
                )
            session.add(DenunciaCategoria(denuncia_id=denuncia_id, categoria_id=cat_id))

    session.add(denuncia)
    await session.flush()
    return await _load_denuncia_full(denuncia_id, session)


@router.patch("/{denuncia_id}/status", response_model=DenunciaReadFull)
async def atualizar_status_denuncia(
    denuncia_id: int,
    situacao: SituacaoEnum,
    descricao: str | None = Query(default=None, description="Observação sobre a mudança de status"),
    session: AsyncSession = Depends(get_session),
) -> Denuncia:
    """Atualiza o status (situação) de uma denúncia."""
    result = await session.execute(select(Denuncia).where(Denuncia.id == denuncia_id))
    denuncia = result.scalar_one_or_none()
    if not denuncia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Denúncia não encontrada.")

    if denuncia.status_id:
        st = await session.get(Status, denuncia.status_id)
        if st:
            st.situacao = situacao
            st.updated_at = datetime.utcnow()
            if descricao:
                st.descricao = descricao
            session.add(st)
    else:
        st = Status(situacao=situacao, descricao=descricao)
        session.add(st)
        await session.flush()
        denuncia.status_id = st.id
        session.add(denuncia)

    await session.flush()
    return await _load_denuncia_full(denuncia_id, session)


@router.delete("/{denuncia_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remover_denuncia(
    denuncia_id: int,
    session: AsyncSession = Depends(get_session),
) -> None:
    """Remove uma denúncia e seus dados relacionados."""
    result = await session.execute(select(Denuncia).where(Denuncia.id == denuncia_id))
    denuncia = result.scalar_one_or_none()
    if not denuncia:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Denúncia não encontrada.")
    await session.delete(denuncia)
