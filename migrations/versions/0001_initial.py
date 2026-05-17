"""criacao inicial das tabelas

Revision ID: 0001_initial
Revises: 
Create Date: 2025-05-17 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
import sqlmodel
from alembic import op

# revision identifiers
revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Tabela: usuario
    op.create_table(
        "usuario",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sqlmodel.AutoString(length=120), nullable=False),
        sa.Column("email", sqlmodel.AutoString(length=255), nullable=False),
        sa.Column("cpf", sqlmodel.AutoString(length=14), nullable=False),
        sa.Column("telefone", sqlmodel.AutoString(length=20), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default="1"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
        sa.UniqueConstraint("cpf"),
    )
    op.create_index("ix_usuario_nome", "usuario", ["nome"])
    op.create_index("ix_usuario_email", "usuario", ["email"])

    # Tabela: categoria
    op.create_table(
        "categoria",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nome", sqlmodel.AutoString(length=100), nullable=False),
        sa.Column("descricao", sqlmodel.AutoString(length=500), nullable=True),
        sa.Column("ativa", sa.Boolean(), nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("nome"),
    )
    op.create_index("ix_categoria_nome", "categoria", ["nome"])

    # Tabela: localizacao
    op.create_table(
        "localizacao",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("logradouro", sqlmodel.AutoString(length=255), nullable=False),
        sa.Column("numero", sqlmodel.AutoString(length=20), nullable=True),
        sa.Column("complemento", sqlmodel.AutoString(length=100), nullable=True),
        sa.Column("bairro", sqlmodel.AutoString(length=100), nullable=False),
        sa.Column("cidade", sqlmodel.AutoString(length=100), nullable=False),
        sa.Column("estado", sqlmodel.AutoString(length=2), nullable=False),
        sa.Column("cep", sqlmodel.AutoString(length=9), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_localizacao_bairro", "localizacao", ["bairro"])
    op.create_index("ix_localizacao_cidade", "localizacao", ["cidade"])
    op.create_index("ix_localizacao_logradouro", "localizacao", ["logradouro"])

    # Tabela: status
    op.create_table(
        "status",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("situacao", sqlmodel.AutoString(), nullable=False),
        sa.Column("descricao", sqlmodel.AutoString(length=500), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_status_situacao", "status", ["situacao"])

    # Tabela: denuncia
    op.create_table(
        "denuncia",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("titulo", sqlmodel.AutoString(length=200), nullable=False),
        sa.Column("descricao", sqlmodel.AutoString(length=2000), nullable=False),
        sa.Column("prioridade", sqlmodel.AutoString(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("localizacao_id", sa.Integer(), nullable=False),
        sa.Column("status_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["usuario_id"], ["usuario.id"]),
        sa.ForeignKeyConstraint(["localizacao_id"], ["localizacao.id"]),
        sa.ForeignKeyConstraint(["status_id"], ["status.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_denuncia_titulo", "denuncia", ["titulo"])
    op.create_index("ix_denuncia_prioridade", "denuncia", ["prioridade"])
    op.create_index("ix_denuncia_usuario_id", "denuncia", ["usuario_id"])
    op.create_index("ix_denuncia_localizacao_id", "denuncia", ["localizacao_id"])

    # Tabela associativa: denuncia_categoria (M:N)
    op.create_table(
        "denuncia_categoria",
        sa.Column("denuncia_id", sa.Integer(), nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["denuncia_id"], ["denuncia.id"]),
        sa.ForeignKeyConstraint(["categoria_id"], ["categoria.id"]),
        sa.PrimaryKeyConstraint("denuncia_id", "categoria_id"),
    )

    # Tabela: atendimento
    op.create_table(
        "atendimento",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("orgao_responsavel", sqlmodel.AutoString(length=200), nullable=False),
        sa.Column("responsavel_nome", sqlmodel.AutoString(length=120), nullable=True),
        sa.Column("observacao", sqlmodel.AutoString(length=1000), nullable=True),
        sa.Column("data_inicio", sa.DateTime(), nullable=False),
        sa.Column("data_conclusao", sa.DateTime(), nullable=True),
        sa.Column("custo_estimado", sa.Float(), nullable=True),
        sa.Column("denuncia_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["denuncia_id"], ["denuncia.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_atendimento_orgao_responsavel", "atendimento", ["orgao_responsavel"])
    op.create_index("ix_atendimento_denuncia_id", "atendimento", ["denuncia_id"])

    # Tabela: document
    op.create_table(
        "document",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sqlmodel.AutoString(length=255), nullable=False),
        sa.Column("content_type", sqlmodel.AutoString(length=100), nullable=False),
        sa.Column("extension", sqlmodel.AutoString(length=10), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("denuncia_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["denuncia_id"], ["denuncia.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_document_denuncia_id", "document", ["denuncia_id"])


def downgrade() -> None:
    op.drop_table("document")
    op.drop_table("atendimento")
    op.drop_table("denuncia_categoria")
    op.drop_table("denuncia")
    op.drop_table("status")
    op.drop_table("localizacao")
    op.drop_table("categoria")
    op.drop_table("usuario")
