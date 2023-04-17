from pathlib import Path
from typing import Dict

from hydrolib.core.basemodel import ModelSaveSettings, SerializerConfig


class XYNSerializer:
    @staticmethod
    def serialize(
        path: Path,
        data: Dict,
        config: SerializerConfig,
        save_settings: ModelSaveSettings,
    ) -> None:
        """
        Serializes the observation point data to an .xyn file at the specified path.

        If the name contains spaces, it will be surrounded with single quotes.

        Args:
            path (Path): The path to the destination file.
            data (Dict[str, List[XYNPoint]]): The data to be serialized.
                The dictionary should contain a single key 'points' that holds a list of XYNPoints.
            config (SerializerConfig): The serialization configuration.
            save_settings (ModelSaveSettings): The model save settings.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        space = 1 * " "
        format_float = lambda x: f"{x:{config.float_format}}"
        format_name = lambda n: f"'{n}'" if " " in n else n

        serialized_points = []

        for point in data["points"]:
            serialized_point: str = space.join(
                [
                    format_float(point.x),
                    format_float(point.y),
                    format_name(point.n),
                ]
            )
            serialized_points.append(serialized_point)

        file_content: str = "\n".join(serialized_points)

        with path.open("w", encoding="utf8") as f:
            f.write(file_content)
