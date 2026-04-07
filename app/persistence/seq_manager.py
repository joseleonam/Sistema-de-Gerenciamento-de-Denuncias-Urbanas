from pathlib import Path


class SeqManager:
    def __init__(self, seq_file: str):
        self.seq_file = Path(seq_file)
        self.seq_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.seq_file.exists():
            self.seq_file.write_text("0", encoding="utf-8")

    def _read(self) -> int:
        text = self.seq_file.read_text(encoding="utf-8").strip()
        try:
            return int(text)
        except ValueError:
            raise ValueError(f"Invalid sequence file value: {text}")

    def _write(self, value: int) -> None:
        self.seq_file.write_text(str(value), encoding="utf-8")

    def current(self) -> int:
        return self._read()

    def next_id(self) -> int:
        current = self._read()
        next_value = current + 1
        self._write(next_value)
        return next_value