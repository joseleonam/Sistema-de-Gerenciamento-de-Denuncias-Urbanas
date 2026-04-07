from enum import Enum

from pydantic import BaseModel


class StatusDenuncia(str, Enum):
    aberta = "ABERTA"
    em_analise = "EM_ANALISE"
    resolvida = "RESOLVIDA"


class StatusBase(BaseModel):
    nome: StatusDenuncia
    descricao: str | None = None


class StatusOut(StatusBase):
    id: int

    class Config:
        from_attributes = True
