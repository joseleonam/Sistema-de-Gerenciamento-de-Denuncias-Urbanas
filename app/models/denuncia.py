from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field
from app.models.status import StatusDenuncia
from app.models.usuario import UsuarioOut


class DenunciaBase(BaseModel):
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

    class Config:
        use_enum_values = True


class DenunciaCreate(DenunciaBase):
    usuario_id: int


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


class DenunciaDB(DenunciaBase):
    id: int

    class Config:
        from_attributes = True
  
class DenunciaOut(DenunciaBase):
    id: int
    usuario: UsuarioOut | None = None

    class Config:
        from_attributes = True