"""
Configuração do banco de dados assíncrono.
Cria engine, sessão e utilitários para uso via FastAPI dependency injection.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import SQLModel

from app.core.config import get_settings

settings = get_settings()

# Cria engine assíncrono
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
)

# Fábrica de sessões assíncronas
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency do FastAPI que fornece uma sessão de banco de dados assíncrona.
    Garante commit/rollback e fechamento automático da sessão.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_db_and_tables() -> None:
    """Cria todas as tabelas no banco (usado apenas em desenvolvimento/testes)."""
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
