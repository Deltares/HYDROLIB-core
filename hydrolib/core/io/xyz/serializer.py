from pathlib import Path
from typing import Dict


class XYZSerializer:
    @staticmethod
    def serialize(path: Path, data: Dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as f:
            for point in data["points"]:
                if point.comment:
                    f.write(f"{point.x} {point.y} {point.z} # {point.comment}\n")
                else:
                    f.write(f"{point.x} {point.y} {point.z}\n")
