"""
Modelos de dados do Sistema de Gerenciamento de Denúncias Urbanas.

Entidades:
- Usuario: cidadão que registra denúncias
- Categoria: tipo de problema (buraco, iluminação, lixo, etc.)
- Localizacao: endereço e coordenadas da ocorrência
- Status: estado atual de uma denúncia
- Denuncia: relato de um problema urbano (many-to-many com Categoria via DenunciaCategoria)
- Atendimento: registro de resposta/ação do órgão público
- Document: metadados de arquivos anexados a denúncias
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


# Tabela associativa: Denuncia ↔ Categoria (M:N)

class DenunciaCategoria(SQLModel, table=True):
    """Tabela associativa entre Denuncia e Categoria (many-to-many)."""

    __tablename__ = "denuncia_categoria"

    denuncia_id: Optional[int] = Field(
        default=None, foreign_key="denuncia.id", primary_key=True
    )
    categoria_id: Optional[int] = Field(
        default=None, foreign_key="categoria.id", primary_key=True
    )


# Enums

class PrioridadeEnum(str, Enum):
    baixa = "baixa"
    media = "media"
    alta = "alta"
    urgente = "urgente"


class SituacaoEnum(str, Enum):
    aberto = "aberto"
    em_analise = "em_analise"
    em_andamento = "em_andamento"
    resolvido = "resolvido"
    arquivado = "arquivado"


# Usuario

class UsuarioBase(SQLModel):
    nome: str = Field(min_length=2, max_length=120, index=True)
    email: str = Field(unique=True, index=True, max_length=255)
    cpf: str = Field(unique=True, max_length=14)
    telefone: Optional[str] = Field(default=None, max_length=20)
    ativo: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Usuario(UsuarioBase, table=True):
    """Cidadão que realiza denúncias."""

    id: Optional[int] = Field(default=None, primary_key=True)

    # Relacionamentos
    denuncias: list["Denuncia"] = Relationship(back_populates="usuario")


class UsuarioCreate(UsuarioBase):
    pass


class UsuarioUpdate(SQLModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    ativo: Optional[bool] = None


class UsuarioRead(UsuarioBase):
    id: int


class UsuarioReadWithDenuncias(UsuarioRead):
    denuncias: list["DenunciaRead"] = []


# Categoria

class CategoriaBase(SQLModel):
    nome: str = Field(unique=True, max_length=100, index=True)
    descricao: Optional[str] = Field(default=None, max_length=500)
    ativa: bool = Field(default=True)


class Categoria(CategoriaBase, table=True):
    """Tipo de problema urbano (buraco, iluminação, lixo, etc.)."""

    id: Optional[int] = Field(default=None, primary_key=True)

    # Relacionamentos
    denuncias: list["Denuncia"] = Relationship(
        back_populates="categorias", link_model=DenunciaCategoria
    )


class CategoriaCreate(CategoriaBase):
    pass


class CategoriaUpdate(SQLModel):
    nome: Optional[str] = None
    descricao: Optional[str] = None
    ativa: Optional[bool] = None


class CategoriaRead(CategoriaBase):
    id: int


# Localizacao

class LocalizacaoBase(SQLModel):
    logradouro: str = Field(max_length=255, index=True)
    numero: Optional[str] = Field(default=None, max_length=20)
    complemento: Optional[str] = Field(default=None, max_length=100)
    bairro: str = Field(max_length=100, index=True)
    cidade: str = Field(max_length=100, index=True)
    estado: str = Field(max_length=2)
    cep: Optional[str] = Field(default=None, max_length=9)
    latitude: Optional[float] = Field(default=None)
    longitude: Optional[float] = Field(default=None)


class Localizacao(LocalizacaoBase, table=True):
    """Endereço e coordenadas geográficas da ocorrência."""

    id: Optional[int] = Field(default=None, primary_key=True)

    # Relacionamentos
    denuncias: list["Denuncia"] = Relationship(back_populates="localizacao")


class LocalizacaoCreate(LocalizacaoBase):
    pass


class LocalizacaoUpdate(SQLModel):
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    complemento: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class LocalizacaoRead(LocalizacaoBase):
    id: int


# Status

class StatusBase(SQLModel):
    situacao: SituacaoEnum = Field(default=SituacaoEnum.aberto, index=True)
    descricao: Optional[str] = Field(default=None, max_length=500)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Status(StatusBase, table=True):
    """Estado atual de uma denúncia."""

    id: Optional[int] = Field(default=None, primary_key=True)

    # Relacionamentos
    denuncia: Optional["Denuncia"] = Relationship(back_populates="status")


class StatusCreate(StatusBase):
    pass


class StatusUpdate(SQLModel):
    situacao: Optional[SituacaoEnum] = None
    descricao: Optional[str] = None


class StatusRead(StatusBase):
    id: int


# Document

class DocumentBase(SQLModel):
    original_filename: str = Field(max_length=255)
    content_type: str = Field(max_length=100)
    extension: str = Field(max_length=10)
    size_bytes: int
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Document(DocumentBase, table=True):
    """Metadados de arquivos (imagens/PDFs) anexados a denúncias."""

    id: Optional[int] = Field(default=None, primary_key=True)
    denuncia_id: Optional[int] = Field(default=None, foreign_key="denuncia.id", index=True)

    # Relacionamentos
    denuncia: Optional["Denuncia"] = Relationship(back_populates="documents")


class DocumentRead(DocumentBase):
    id: int
    denuncia_id: Optional[int]


# Atendimento

class AtendimentoBase(SQLModel):
    orgao_responsavel: str = Field(max_length=200, index=True)
    responsavel_nome: Optional[str] = Field(default=None, max_length=120)
    observacao: Optional[str] = Field(default=None, max_length=1000)
    data_inicio: datetime = Field(default_factory=datetime.utcnow)
    data_conclusao: Optional[datetime] = Field(default=None)
    custo_estimado: Optional[float] = Field(default=None)


class Atendimento(AtendimentoBase, table=True):
    """Registro de resposta/ação do órgão público sobre uma denúncia."""

    id: Optional[int] = Field(default=None, primary_key=True)
    denuncia_id: int = Field(foreign_key="denuncia.id", index=True)

    # Relacionamentos
    denuncia: Optional["Denuncia"] = Relationship(back_populates="atendimentos")


class AtendimentoCreate(AtendimentoBase):
    denuncia_id: int


class AtendimentoUpdate(SQLModel):
    orgao_responsavel: Optional[str] = None
    responsavel_nome: Optional[str] = None
    observacao: Optional[str] = None
    data_conclusao: Optional[datetime] = None
    custo_estimado: Optional[float] = None


class AtendimentoRead(AtendimentoBase):
    id: int
    denuncia_id: int


# Denuncia (entidade central)

class DenunciaBase(SQLModel):
    titulo: str = Field(min_length=5, max_length=200, index=True)
    descricao: str = Field(min_length=10, max_length=2000)
    prioridade: PrioridadeEnum = Field(default=PrioridadeEnum.media, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Denuncia(DenunciaBase, table=True):
    """
    Relato de um problema urbano feito por um cidadão.

    Relacionamentos:
    - many-to-one com Usuario
    - many-to-one com Localizacao
    - one-to-one com Status
    - many-to-many com Categoria (via DenunciaCategoria)
    - one-to-many com Atendimento
    - one-to-many com Document
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    usuario_id: int = Field(foreign_key="usuario.id", index=True)
    localizacao_id: int = Field(foreign_key="localizacao.id", index=True)
    status_id: Optional[int] = Field(default=None, foreign_key="status.id")

    # Relacionamentos
    usuario: Optional[Usuario] = Relationship(back_populates="denuncias")
    localizacao: Optional[Localizacao] = Relationship(back_populates="denuncias")
    status: Optional[Status] = Relationship(
        back_populates="denuncia",
        sa_relationship_kwargs={"foreign_keys": "[Denuncia.status_id]"},
    )
    categorias: list[Categoria] = Relationship(
        back_populates="denuncias", link_model=DenunciaCategoria
    )
    atendimentos: list[Atendimento] = Relationship(back_populates="denuncia")
    documents: list[Document] = Relationship(back_populates="denuncia")


class DenunciaCreate(DenunciaBase):
    usuario_id: int
    localizacao_id: int
    categoria_ids: list[int] = []


class DenunciaUpdate(SQLModel):
    titulo: Optional[str] = None
    descricao: Optional[str] = None
    prioridade: Optional[PrioridadeEnum] = None
    localizacao_id: Optional[int] = None
    categoria_ids: Optional[list[int]] = None


class DenunciaRead(DenunciaBase):
    id: int
    usuario_id: int
    localizacao_id: int
    status_id: Optional[int]


class DenunciaReadFull(DenunciaRead):
    usuario: Optional[UsuarioRead] = None
    localizacao: Optional[LocalizacaoRead] = None
    status: Optional[StatusRead] = None
    categorias: list[CategoriaRead] = []
    atendimentos: list[AtendimentoRead] = []
    documents: list[DocumentRead] = []


# Forward refs
UsuarioReadWithDenuncias.model_rebuild()
