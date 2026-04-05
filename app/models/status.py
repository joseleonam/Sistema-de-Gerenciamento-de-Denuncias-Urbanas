from enum import Enum

from pydantic import BaseModel


class StatusDenuncia(str, Enum):
    aberta = "aberta"
    em_analise = "em_analise"
    resolvida = "resolvida"


class StatusBase(BaseModel):
    nome: StatusDenuncia
    descricao: str | None = None


class StatusOut(StatusBase):
    id: int

    class Config:
        from_attributes = True
