from pathlib import Path
from typing import Dict


class DummySerializer:
    @staticmethod
    def serialize(path: Path, data: Dict, config, save_settings) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf8") as f:
            f.write(str(data))
