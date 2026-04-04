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

        if not self.table_path.exists():
            # Create an empty delta table, no commit will record rows until insert.
            empty = pd.DataFrame(columns=self._columns())
            write_deltalake(str(self.table_path), empty, mode="overwrite")

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
        if "data_atualizacao" in self._columns() and "data_atualizacao" not in data:
            data["data_atualizacao"] = None

        df = pd.DataFrame([data])
        write_deltalake(str(self.table_path), df, mode="append")
        return self.model(**data)

    def get(self, record_id: int) -> Optional[T]:
        table = self._table()
        batch = table.to_pyarrow_table(filters=[["id", "=", record_id]])
        if batch.num_rows == 0:
            return None
        df = batch.to_pandas()
        row = df.iloc[0].to_dict()
        return self.model(**row)

    def list(self, page: int = 1, page_size: int = 20) -> List[T]:
        table = self._table()
        pyarrow_table = table.to_pyarrow_table()
        batches = pyarrow_table.to_batches(max_chunksize=page_size)

        start = (page - 1) * page_size
        stop = start + page_size
        collected = []
        idx = 0
        for batch in batches:
            batch_df = batch.to_pandas()
            for _, row in batch_df.iterrows():
                if idx >= start and idx < stop:
                    collected.append(self.model(**row.to_dict()))
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
        return table.to_pyarrow_table().num_rows

    def vacuum(self, retention_hours: Optional[int] = None) -> List[str]:
        table = self._table()
        return table.vacuum(dry_run=False, retention_hours=retention_hours)
