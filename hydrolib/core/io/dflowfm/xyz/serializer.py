from pathlib import Path
from typing import Dict

from hydrolib.core.basemodel import SerializerConfig


class XYZSerializer:
    @staticmethod
    def serialize(path: Path, data: Dict, config: SerializerConfig) -> None:
        """
        Serializes the XYZ data to the file at the specified path.

        Attributes:
            path (Path): The path to the destination file.
            data (Dict): The data to be serialized.
            config (SerializerConfig): The serialization configuration.
        """
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w") as f:
            for point in data["points"]:
                if point.comment:
                    f.write(f"{point.x} {point.y} {point.z} # {point.comment}\n")
                else:
                    f.write(f"{point.x} {point.y} {point.z}\n")
