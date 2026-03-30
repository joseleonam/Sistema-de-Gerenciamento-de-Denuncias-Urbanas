from pydantic import BaseModel, Field


class CategoriaBase(BaseModel):
    nome: str = Field(min_length=3, max_length=80)
    descricao: str | None = Field(default=None, max_length=250)


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=3, max_length=80)
    descricao: str | None = Field(default=None, max_length=250)

    class Config:
        orm_mode = True


class CategoriaOut(CategoriaBase):
    id: int

    class Config:
        orm_mode = True
