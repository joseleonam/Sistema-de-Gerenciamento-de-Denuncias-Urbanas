from .delta_storage import DeltaRepository
from ..models.denuncia import DenunciaCreate, DenunciaUpdate, DenunciaDB


class DenunciaRepository(DeltaRepository[DenunciaDB]):
    def __init__(self, table_path: str = "data/denuncias", seq_file: str = "data/denuncias.seq"):
        super().__init__(table_path=table_path, model=DenunciaDB, seq_file=seq_file)

    def insert_denuncia(self, denuncia: DenunciaCreate) -> DenunciaDB:
        return self.insert(denuncia)

    def get_denuncia(self, id_: int) -> DenunciaDB | None:
        return self.get(id_)

    def list_denuncias(self, page: int = 1, page_size: int = 20):
        return self.list(page=page, page_size=page_size)

    def update_denuncia(self, id_: int, update: DenunciaUpdate) -> DenunciaDB | None:
        data = {k: v for k, v in update.model_dump(exclude_none=True).items()}
        if not data:
            return self.get(id_)
        return self.update(id_, data)

    def delete_denuncia(self, id_: int) -> bool:
        return self.delete(id_)

    def count_denuncias(self) -> int:
        return self.count()

    def vacuum_denuncias(self, retention_hours: int | None):
        return self.vacuum(retention_hours=retention_hours)