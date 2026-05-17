# Sistema de Gerenciamento de Denúncias Urbanas

API RESTful para registro e acompanhamento de problemas urbanos (buracos, iluminação, lixo, etc.) por órgãos públicos.

## Tecnologias

- **FastAPI** — framework web assíncrono
- **SQLModel** — ORM integrando SQLAlchemy + Pydantic
- **Alembic** — migrações de banco de dados
- **fastapi-pagination** — paginação automática
- **uv** — gerenciador de dependências
- **Faker pt_BR** — geração de dados realistas

## Pré-requisitos

- Python 3.11+
- [uv](https://docs.astral.sh/uv/) instalado

## Instalação e Execução

```bash
# 1. Instalar dependências
uv sync
# 2. Configurar o banco (editar .env se necessário)
# Por padrão usa SQLite local
# 3. Executar as migrações
uv run alembic upgrade head
# 4. Popular o banco com dados de teste
uv run python seed.py
# 5. Iniciar o servidor
uv run uvicorn app.main:app --reload
```

A API estará disponível em: http://localhost:8000

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Configuração do Banco de Dados

Edite o arquivo `.env` para alternar entre SQLite e PostgreSQL:

```env
# SQLite (padrão)
DATABASE_URL=sqlite+aiosqlite:///./denuncias_urbanas.db

# PostgreSQL (Neon/Supabase) — descomente para usar
# DATABASE_URL=postgresql+asyncpg://usuario:senha@host:5432/denuncias_urbanas
```

## Estrutura do Projeto

```
denuncias_urbanas/
├── app/
│   ├── core/
│   │   ├── config.py       # Configurações via .env
│   │   └── database.py     # Engine e sessão assíncrona
│   ├── models/
│   │   └── models.py       # Entidades SQLModel
│   ├── routers/
│   │   ├── usuarios.py
│   │   ├── categorias.py
│   │   ├── localizacoes.py
│   │   ├── status.py
│   │   ├── denuncias.py
│   │   ├── atendimentos.py
│   │   └── documents.py
│   └── main.py             # App FastAPI
├── migrations/
│   ├── versions/
│   │   └── 0001_initial.py
│   ├── env.py
│   └── script.py.mako
├── uploads/                # Arquivos enviados (não versionar)
├── seed.py                 # Script de carga de dados
├── alembic.ini
├── pyproject.toml
├── .env
└── .python-version
```

## Entidades e Relacionamentos

| Entidade | Tipo | Relacionamentos |
|----------|------|-----------------|
| Usuario | Principal | 1:N com Denuncia |
| Categoria | Classificação | M:N com Denuncia |
| Localizacao | Endereço | 1:N com Denuncia |
| Status | Estado | 1:1 com Denuncia |
| Denuncia | Central | many-to-one (Usuario, Localizacao, Status), M:N (Categoria), 1:N (Atendimento, Document) |
| Atendimento | Resposta | N:1 com Denuncia |
| Document | Arquivo | N:1 com Denuncia |

## Principais Endpoints

### Denúncias
- `POST /api/v1/denuncias` — criar denúncia
- `GET /api/v1/denuncias` — listar (filtros: titulo, prioridade, situacao, categoria_id, bairro, ano)
- `GET /api/v1/denuncias/{id}` — obter com dados completos
- `PATCH /api/v1/denuncias/{id}/status` — atualizar situação
- `GET /api/v1/denuncias/estatisticas/total` — total de denúncias
- `GET /api/v1/denuncias/estatisticas/por-categoria` — agrupamento por categoria
- `GET /api/v1/denuncias/estatisticas/por-bairro` — bairros com mais problemas

### Documentos
- `POST /api/v1/denuncias/{id}/documents` — upload de imagem/PDF
- `GET /api/v1/denuncias/{id}/documents` — listar documentos
- `GET /api/v1/documents/{id}/download` — baixar arquivo
- `PUT /api/v1/documents/{id}` — substituir arquivo
- `DELETE /api/v1/documents/{id}` — remover documento

## Formatos de arquivo aceitos

- Imagens: JPEG, PNG, GIF
- Documentos: PDF
- Tamanho máximo: 10MB (configurável no .env)
