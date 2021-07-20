from pathlib import Path
from typing import Dict


class DummmyParser:
    @staticmethod
    def parse(filepath: Path) -> Dict:
        return {}


class DummySerializer:
    @staticmethod
    def serialize(path: Path, data: Dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as f:
            f.write(str(data))
