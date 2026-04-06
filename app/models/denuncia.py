from datetime import datetime

from pydantic import BaseModel, Field
from app.models.status import StatusDenuncia


class DenunciaBase(BaseModel):
    id: int | None = None
    titulo: str
    descricao: str
    categoria: str
    endereco: str
    bairro: str
    cidade: str
    uf: str
    status: StatusDenuncia = Field(default=StatusDenuncia.aberta)
    data_criacao: datetime | None = None
    data_atualizacao: datetime | None = None
    usuario_id: int

    class Config:
        use_enum_values = True


class DenunciaCreate(DenunciaBase):
    pass


class DenunciaUpdate(BaseModel):
    titulo: str | None = None
    descricao: str | None = None
    categoria: str | None = None
    endereco: str | None = None
    bairro: str | None = None
    cidade: str | None = None
    uf: str | None = None
    status: StatusDenuncia | None = None
    usuario_id: int | None = None

    class Config:
        use_enum_values = True

class DenunciaOut(DenunciaBase):
    id: int

    class Config:
        from_attributes = True