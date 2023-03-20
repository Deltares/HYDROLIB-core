from pathlib import Path
from typing import Dict

from hydrolib.core.basemodel import SerializerConfig


class XYNSerializer:
    @staticmethod
    def serialize(path: Path, data: Dict, config: SerializerConfig) -> None:
        """
        Serializes the XYN data to the file at the specified path.

        If the name contains spaces, it will be surrounded with single quotes.

        Attributes:
            path (Path): The path to the destination file.
            data (Dict): The data to be serialized.
            config (SerializerConfig): The serialization configuration.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        space = 1 * " "
        format_float = lambda x: f"{x:{config.float_format}}"
        format_name = lambda n: f"'{n}'" if " " in n else n

        with path.open("w") as f:
            for point in data["points"]:
                line: str = space.join(
                    [
                        format_float(point.x),
                        format_float(point.y),
                        format_name(point.n),
                    ]
                )
                f.write(f"{line}\n")
