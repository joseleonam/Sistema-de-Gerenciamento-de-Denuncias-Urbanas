from datetime import datetime

from pydantic import BaseModel


class AtendimentoBase(BaseModel):
    denuncia_id: int
    responsavel: str | None = None
    observacao: str | None = None
    data_atendimento: datetime
    concluido: bool = False


class AtendimentoCreate(AtendimentoBase):
    pass


class AtendimentoUpdate(BaseModel):
    responsavel: str | None = None
    observacao: str | None = None
    data_atendimento: datetime | None = None
    concluido: bool | None = None

    class Config:
        from_attributes = True


class AtendimentoOut(AtendimentoBase):
    id: int

    class Config:
        from_attributes = True
