"""
Script de carga de dados realistas para o Sistema de Denúncias Urbanas.
Utiliza Faker com localização pt_BR para gerar dados consistentes.
Popula no mínimo 100 registros por entidade.

Uso:
    uv run python seed.py

O banco de dados utilizado é o configurado no .env (DATABASE_URL).
"""

import asyncio
import random
from datetime import datetime, timedelta

from faker import Faker
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlmodel import select

from app.core.config import get_settings
from app.models.models import (
    Atendimento,
    Categoria,
    Denuncia,
    DenunciaCategoria,
    Localizacao,
    PrioridadeEnum,
    SituacaoEnum,
    Status,
    Usuario,
)

fake = Faker("pt_BR")
settings = get_settings()

# ─────────────────────────────────────────────
# Dados contextuais para o domínio
# ─────────────────────────────────────────────

CATEGORIAS_DATA = [
    ("Buracos e Pavimentação", "Problemas com buracos, remendos e deterioração do asfalto"),
    ("Iluminação Pública", "Postes apagados, lâmpadas queimadas ou falta de iluminação"),
    ("Coleta de Lixo", "Falhas na coleta regular de resíduos domésticos"),
    ("Lixo Irregular", "Descarte irregular de lixo em locais não autorizados"),
    ("Alagamento e Drenagem", "Pontos de alagamento, bueiros entupidos e problemas de drenagem"),
    ("Calçadas e Acessibilidade", "Calçadas danificadas, irregulares ou sem acessibilidade"),
    ("Arborização Urbana", "Árvores com risco de queda, galhos perigosos ou poda necessária"),
    ("Água e Esgoto", "Vazamentos de água, esgoto a céu aberto ou falta de saneamento"),
    ("Sinalização de Trânsito", "Placas danificadas, semáforos com defeito ou faixas apagadas"),
    ("Edificações em Risco", "Prédios ou muros com risco de desabamento"),
    ("Vandalismo", "Depredação de mobiliário urbano, pichações e danos ao patrimônio"),
    ("Fauna Urbana", "Animais soltos, pombos em excesso, roedores ou outros animais perigosos"),
]

ORGAOS = [
    "Secretaria de Infraestrutura Urbana",
    "SEUMA - Secretaria de Urbanismo e Meio Ambiente",
    "EMLURB - Empresa de Limpeza Urbana",
    "CAGECE - Companhia de Água e Esgoto",
    "ENEL - Distribuição de Energia",
    "DETRAN-CE",
    "AMC - Autarquia Municipal de Trânsito",
    "Defesa Civil Municipal",
    "Secretaria de Saúde",
    "SEMACE - Superintendência do Meio Ambiente",
]

BAIRROS_FORTALEZA = [
    "Centro", "Meireles", "Aldeota", "Varjota", "Mucuripe",
    "Bairro de Fátima", "Benfica", "Montese", "Parangaba", "Messejana",
    "Maraponga", "Mondubim", "Bom Jardim", "Granja Lisboa", "Granja Portugal",
    "Conjunto Ceará", "Jangurussu", "Barroso", "Ancuri", "Passaré",
    "Cocó", "Guararapes", "Água Fria", "Itaperi", "Serrinha",
    "Parquelândia", "Amadeu Furtado", "Damas", "Fátima", "Antônio Bezerra",
]

LOGRADOUROS_TIPOS = ["Rua", "Avenida", "Travessa", "Alameda", "Praça"]

TITULOS_BASE = [
    "Buraco profundo na {tipo} {nome} causa acidentes",
    "Poste sem iluminação há {dias} dias no bairro {bairro}",
    "Lixo acumulado na esquina da {tipo} {nome} com {nome2}",
    "Alagamento recorrente na {tipo} {nome} durante chuvas",
    "Calçada destruída impede passagem de cadeirantes na {bairro}",
    "Árvore com risco de queda na {tipo} {nome} número {num}",
    "Vazamento de esgoto na {tipo} {nome} há {dias} dias",
    "Semáforo com defeito causa congestionamento na {bairro}",
    "Muro com risco de desabamento na {tipo} {nome}",
    "Pichação extensa em muro histórico no {bairro}",
]


def random_date(start_year: int = 2023, end_year: int = 2025) -> datetime:
    start = datetime(start_year, 1, 1)
    end = datetime(end_year, 12, 31)
    delta = end - start
    return start + timedelta(days=random.randint(0, delta.days))


def gerar_cpf() -> str:
    """Gera um CPF formatado (não necessariamente válido, apenas para dados de teste)."""
    nums = [random.randint(0, 9) for _ in range(11)]
    return f"{''.join(map(str, nums[:3]))}.{''.join(map(str, nums[3:6]))}.{''.join(map(str, nums[6:9]))}-{''.join(map(str, nums[9:]))}"


async def seed(session: AsyncSession) -> None:
    print("🌱 Iniciando carga de dados...")

    # ── 1. Categorias (12 fixas + contextuais) ──────────────────────────
    print("  📂 Criando categorias...")
    categorias = []
    for nome, descricao in CATEGORIAS_DATA:
        cat = Categoria(nome=nome, descricao=descricao, ativa=True)
        session.add(cat)
        categorias.append(cat)
    await session.flush()
    print(f"     ✓ {len(categorias)} categorias criadas")

    # ── 2. Usuários (150) ────────────────────────────────────────────────
    print("  👤 Criando usuários...")
    usuarios = []
    emails_usados = set()
    cpfs_usados = set()
    for i in range(150):
        while True:
            email = fake.email()
            if email not in emails_usados:
                emails_usados.add(email)
                break
        while True:
            cpf = gerar_cpf()
            if cpf not in cpfs_usados:
                cpfs_usados.add(cpf)
                break
        u = Usuario(
            nome=fake.name(),
            email=email,
            cpf=cpf,
            telefone=fake.phone_number()[:20],
            ativo=random.random() > 0.05,
            created_at=random_date(2022, 2024),
        )
        session.add(u)
        usuarios.append(u)
    await session.flush()
    print(f"     ✓ {len(usuarios)} usuários criados")

    # ── 3. Localizações (150) ─────────────────────────────────────────────
    print("  📍 Criando localizações...")
    localizacoes = []
    for _ in range(150):
        bairro = random.choice(BAIRROS_FORTALEZA)
        tipo = random.choice(LOGRADOUROS_TIPOS)
        loc = Localizacao(
            logradouro=f"{tipo} {fake.last_name()}",
            numero=str(random.randint(1, 9999)) if random.random() > 0.1 else None,
            complemento=random.choice([None, "Próximo ao mercado", "Em frente à escola", "Esquina"]),
            bairro=bairro,
            cidade="Fortaleza",
            estado="CE",
            cep=f"{random.randint(60000, 60999):05d}-{random.randint(0, 999):03d}",
            latitude=round(random.uniform(-3.85, -3.68), 6),
            longitude=round(random.uniform(-38.65, -38.40), 6),
        )
        session.add(loc)
        localizacoes.append(loc)
    await session.flush()
    print(f"     ✓ {len(localizacoes)} localizações criadas")

    # ── 4. Status + Denúncias (150) ────────────────────────────────────────
    print("  📋 Criando denúncias e status...")
    denuncias = []
    for i in range(150):
        situacao = random.choices(
            list(SituacaoEnum),
            weights=[30, 20, 25, 20, 5],  # mais abertos e em andamento
        )[0]
        criado_em = random_date(2023, 2025)

        # Status
        st = Status(
            situacao=situacao,
            descricao=random.choice([
                "Aguardando triagem pela equipe técnica.",
                "Vistoria agendada para a próxima semana.",
                "Equipe de campo acionada.",
                "Problema solucionado conforme registro.",
                "Denúncia encaminhada ao órgão competente.",
                None,
            ]),
            updated_at=criado_em + timedelta(days=random.randint(0, 30)),
        )
        session.add(st)
        await session.flush()

        prioridade = random.choices(
            list(PrioridadeEnum),
            weights=[20, 40, 30, 10],
        )[0]

        bairro = random.choice(BAIRROS_FORTALEZA)
        nome_rua = fake.last_name()
        tipo = random.choice(LOGRADOUROS_TIPOS)
        titulo = random.choice([
            f"Buraco na {tipo} {nome_rua} causa risco para motoristas",
            f"Falta de iluminação na {tipo} {nome_rua} no bairro {bairro}",
            f"Acúmulo de lixo no {bairro} há vários dias",
            f"Alagamento recorrente na {tipo} {nome_rua}",
            f"Calçada danificada no {bairro} impede locomoção",
            f"Árvore com risco de queda na {tipo} {nome_rua}",
            f"Vazamento de água na {tipo} {nome_rua} número {random.randint(1, 500)}",
            f"Semáforo quebrado no cruzamento do {bairro}",
            f"Esgoto a céu aberto na {tipo} {nome_rua}",
            f"Pichação em equipamento público no {bairro}",
        ])

        d = Denuncia(
            titulo=titulo,
            descricao=fake.paragraph(nb_sentences=random.randint(2, 5)),
            prioridade=prioridade,
            created_at=criado_em,
            updated_at=criado_em + timedelta(days=random.randint(0, 10)),
            usuario_id=random.choice(usuarios).id,
            localizacao_id=random.choice(localizacoes).id,
            status_id=st.id,
        )
        session.add(d)
        denuncias.append(d)

    await session.flush()
    print(f"     ✓ {len(denuncias)} denúncias criadas")

    # ── 5. Associações Denuncia ↔ Categoria (many-to-many) ──────────────
    print("  🔗 Associando denúncias às categorias...")
    assoc_count = 0
    for d in denuncias:
        num_cats = random.randint(1, 3)
        cats_escolhidas = random.sample(categorias, k=min(num_cats, len(categorias)))
        for cat in cats_escolhidas:
            dc = DenunciaCategoria(denuncia_id=d.id, categoria_id=cat.id)
            session.add(dc)
            assoc_count += 1
    await session.flush()
    print(f"     ✓ {assoc_count} associações criadas")

    # ── 6. Atendimentos (120) ──────────────────────────────────────────────
    print("  🔧 Criando atendimentos...")
    atendimentos_count = 0
    denuncias_com_atendimento = random.sample(denuncias, k=min(120, len(denuncias)))
    for d in denuncias_com_atendimento:
        num_at = random.randint(1, 3)
        for j in range(num_at):
            data_inicio = d.created_at + timedelta(days=random.randint(1, 15))
            concluido = random.random() > 0.4
            at = Atendimento(
                orgao_responsavel=random.choice(ORGAOS),
                responsavel_nome=fake.name() if random.random() > 0.3 else None,
                observacao=fake.sentence(nb_words=12) if random.random() > 0.2 else None,
                data_inicio=data_inicio,
                data_conclusao=(
                    data_inicio + timedelta(days=random.randint(1, 30))
                    if concluido else None
                ),
                custo_estimado=(
                    round(random.uniform(500, 50000), 2)
                    if random.random() > 0.3 else None
                ),
                denuncia_id=d.id,
            )
            session.add(at)
            atendimentos_count += 1

    await session.flush()
    print(f"     ✓ {atendimentos_count} atendimentos criados")

    await session.commit()
    print("\n✅ Carga concluída com sucesso!")
    print(f"   • {len(categorias)} categorias")
    print(f"   • {len(usuarios)} usuários")
    print(f"   • {len(localizacoes)} localizações")
    print(f"   • {len(denuncias)} denúncias (com status)")
    print(f"   • {assoc_count} associações denuncia-categoria")
    print(f"   • {atendimentos_count} atendimentos")


async def main() -> None:
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        await seed(session)
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
