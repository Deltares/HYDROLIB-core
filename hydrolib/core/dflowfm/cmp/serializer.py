from pathlib import Path
from typing import Any, Dict, List

from hydrolib.core.basemodel import ModelSaveSettings


class CmpSerializer:
    @staticmethod
    def serialize(
        path: Path,
        data: Dict[str, List[Any]],
        save_settings: ModelSaveSettings,
    ) -> None:
        return
