from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Generic, List, Optional, Type, TypeVar

import pandas as pd
from deltalake import DeltaTable, write_deltalake
from pydantic import BaseModel

from .seq_manager import SeqManager

T = TypeVar("T", bound=BaseModel)


class DeltaRepository(Generic[T]):
    def __init__(self, table_path: str, model: Type[T], seq_file: Optional[str] = None):
        self.table_path = Path(table_path)
        self.model = model
        self.seq = SeqManager(seq_file or f"{self.table_path}.seq")

    def _columns(self) -> List[str]:
        return list(self.model.schema().get("properties", {}).keys())

    def _table(self) -> DeltaTable:
        return DeltaTable(str(self.table_path))

    def insert(self, item: T) -> T:
        data = item.model_dump(exclude_none=True)
        new_id = self.seq.next_id()
        data["id"] = new_id

        now = datetime.utcnow()
        if "data_criacao" in self._columns() and "data_criacao" not in data:
            data["data_criacao"] = now

         # ❌ NÃO definir data_atualizacao aqui

        df = pd.DataFrame([data])
        write_deltalake(str(self.table_path), df, mode="append")
        return self.model(**data)

    def get(self, record_id: int) -> T | None:
        table = self._table()

        for batch in table.to_batches():
            rows = batch.to_pylist()

            for row in rows:
                if row.get("id") == record_id:
                    return self.model(**row)

        return None

    def list(self, page: int = 1, page_size: int = 20) -> list[T]:
        table = self._table()

        start = (page - 1) * page_size
        stop = start + page_size

        collected = []
        idx = 0

        for batch in table.to_batches():
            for row in batch.to_pylist():
                if start <= idx < stop:
                    collected.append(self.model(**row))
                idx += 1
                if idx >= stop:
                    break
            if idx >= stop:
                break

        return collected

    def update(self, record_id: int, data: dict) -> Optional[T]:
        table = self._table()
        existing = table.to_pyarrow_table(filters=[["id", "=", record_id]])
        if existing.num_rows == 0:
            return None

        data["data_atualizacao"] = datetime.utcnow()
        table.update(predicate=f"id = {record_id}", new_values=data)

        return self.get(record_id)

    def delete(self, record_id: int) -> bool:
        table = self._table()
        result = table.delete(predicate=f"id = {record_id}")
        return result.get("num_updated_rows", 0) > 0 or result.get("num_removed_files", 0) > 0

    def count(self) -> int:
        table = self._table()
        return sum(batch.num_rows for batch in table.to_batches())

    def vacuum(self, retention_hours: Optional[int] = None) -> List[str]:
        table = self._table()
        return table.vacuum(dry_run=False, retention_hours=retention_hours)
