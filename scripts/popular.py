from faker import Faker
from datetime import datetime
import random

from app.persistence.denuncia_repository import DenunciaRepository
from app.models.denuncia import DenunciaCreate
from app.models.status import StatusDenuncia

fake = Faker("pt_BR")

repo = DenunciaRepository()

CATEGORIAS = [
    "Buraco",
    "Iluminação",
    "Lixo",
    "Esgoto",
    "Trânsito",
    "Segurança"
]

STATUS = [
    StatusDenuncia.aberta,
    StatusDenuncia.em_analise,
    StatusDenuncia.resolvida
]


def gerar_denuncia():
    return DenunciaCreate(
        titulo=fake.sentence(nb_words=6),
        descricao=fake.text(max_nb_chars=200),
        categoria=random.choice(CATEGORIAS),
        endereco=fake.street_address(),
        bairro=fake.bairro(),
        cidade="Fortaleza",
        uf="CE",
        usuario_id=random.randint(1, 50)
    )


def main():
    total = 1000

    print(f"Inserindo {total} denúncias...")

    for i in range(total):
        denuncia = gerar_denuncia()
        repo.insert_denuncia(denuncia)

        if i % 100 == 0:
            print(f"{i} registros inseridos...")

    print("✔ Inserção concluída!")


if __name__ == "__main__":
    main()