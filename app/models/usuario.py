from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class UsuarioBase(BaseModel):
    nome: str = Field(min_length=3, max_length=120)
    email: EmailStr
    telefone: str | None = Field(default=None, min_length=8, max_length=20)


class UsuarioCreate(UsuarioBase):
    pass


class UsuarioUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=3, max_length=120)
    email: EmailStr | None = None
    telefone: str | None = Field(default=None, min_length=8, max_length=20)

    class Config:
        from_attributes = True


class UsuarioOut(UsuarioBase):
    id: int
    data_criacao: datetime

    class Config:
        from_attributes = True
