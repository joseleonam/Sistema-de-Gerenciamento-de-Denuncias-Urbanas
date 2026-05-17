"""
Sistema de Gerenciamento de Denúncias Urbanas
API RESTful desenvolvida com FastAPI + SQLModel + Alembic

Entidades: Usuario, Denuncia, Categoria, Localizacao, Status, Atendimento, Document
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_pagination import add_pagination
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.routers import atendimentos, categorias, denuncias, documents, localizacoes, status as status_router, usuarios

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Eventos de inicialização e encerramento da aplicação."""
    # Garante que a pasta de uploads existe ao iniciar
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
## Sistema de Gerenciamento de Denúncias Urbanas""",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# Handlers globais de exceção
# ─────────────────────────────────────────────

@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError) -> JSONResponse:
    """Trata erros de integridade do banco (ex.: violação de unique constraint)."""
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": "Violação de integridade: registro duplicado ou referência inválida."},
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """Trata erros de validação de dados."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handler genérico para exceções não tratadas."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Erro interno do servidor. Tente novamente mais tarde."},
    )


# ─────────────────────────────────────────────
# Routers
# ─────────────────────────────────────────────

app.include_router(usuarios.router, prefix="/api/v1")
app.include_router(categorias.router, prefix="/api/v1")
app.include_router(localizacoes.router, prefix="/api/v1")
app.include_router(status_router.router, prefix="/api/v1")
app.include_router(denuncias.router, prefix="/api/v1")
app.include_router(atendimentos.router, prefix="/api/v1")
app.include_router(documents.router, prefix="/api/v1")

# Habilita paginação global
add_pagination(app)


# ─────────────────────────────────────────────
# Rota raiz
# ─────────────────────────────────────────────

@app.get("/", tags=["Saúde"])
async def root() -> dict:
    """Endpoint de verificação de saúde da API."""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "online",
        "docs": "/docs",
        "redoc": "/redoc",
    }


@app.get("/health", tags=["Saúde"])
async def health_check() -> dict:
    """Verifica se a API está funcionando corretamente."""
    return {"status": "healthy"}
