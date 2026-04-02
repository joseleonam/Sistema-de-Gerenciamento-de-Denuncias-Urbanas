from fastapi import FastAPI

from app.api.denuncia_routes import router as denuncia_router
from app.api.hash_routes import router as hash_router

app = FastAPI(
    title="Sistema de Gerenciamento de Denúncias Urbanas",
    version="0.1.0",
    description="API de exemplo usando Delta Lake para persistência de denúncias urbanas",
)

app.include_router(denuncia_router, prefix="/denuncias", tags=["denuncias"])
app.include_router(hash_router, prefix="/hash", tags=["hash"])


@app.get("/")
def root():
    return {"message": "Bem-vindo à API de Denúncias Urbanas"}
