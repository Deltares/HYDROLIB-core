from pathlib import Path
from typing import Dict, Generator

from hydrolib.core.base.models import ModelSaveSettings, SerializerConfig


class XYZSerializer:
    @staticmethod
    def serialize(
        path: Path,
        data: Dict,
        config: SerializerConfig,
        save_settings: ModelSaveSettings,
    ) -> None:
        """
        Serializes the XYZ data to the file at the specified path.

        Attributes:
            path (Path): The path to the destination file.
            data (Dict): The data to be serialized.
            config (SerializerConfig): The serialization configuration.
            save_settings (ModelSaveSettings): The model save settings.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        space = 1 * " "
        format_float = lambda x: f"{x:{config.float_format}}"

        with path.open("w", encoding="utf8") as f:
            for point in data["points"]:
                geometry: str = space.join(
                    [format_float(p) for p in XYZSerializer._get_point_values(point)]
                )
                if point.comment:
                    f.write(f"{geometry} # {point.comment}\n")
                else:
                    f.write(f"{geometry}\n")

    @staticmethod
    def _get_point_values(point) -> Generator[float, None, None]:
        yield point.x
        yield point.y
        yield point.z
