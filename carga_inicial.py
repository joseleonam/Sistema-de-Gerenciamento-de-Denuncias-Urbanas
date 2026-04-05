from faker import Faker
import random
from datetime import datetime, timezone
from app.models.denuncia import DenunciaCreate, StatusDenuncia
from app.persistence.denuncia_repository import DenunciaRepository

fake = Faker('pt_BR')
repo = DenunciaRepository()

def popular_banco(quantidade: int = 1000):
    print(f"Iniciando a inserção de {quantidade} registros...")
    
    categorias = ["Buraco na via", "Iluminação pública", "Lixo acumulado", "Vazamento de água", "Poda de árvore", "Poluição sonora"]
    status_opcoes = [StatusDenuncia.aberta, StatusDenuncia.em_analise, StatusDenuncia.resolvida]
    
    for i in range(quantidade):
        nova_denuncia = DenunciaCreate(
            titulo=fake.sentence(nb_words=4)[:-1], # Tira o ponto final
            descricao=fake.paragraph(nb_sentences=2),
            categoria=random.choice(categorias),
            endereco=fake.street_address(),
            bairro=fake.bairro(),
            cidade=fake.city(),
            uf=fake.estado_sigla(),
            status=random.choice(status_opcoes),
            usuario_id=random.randint(1, 500),
            data_criacao=datetime.now(timezone.utc) # <- INSERINDO A DATA AQUI
        )
        repo.insert_denuncia(nova_denuncia)
        
        if (i + 1) % 100 == 0:
            print(f"{i + 1} registros inseridos...")

    print("Carga inicial concluída com sucesso!")

if __name__ == "__main__":
    popular_banco(1000)