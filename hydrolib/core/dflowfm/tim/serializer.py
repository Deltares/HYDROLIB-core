from pathlib import Path
from typing import Dict

from hydrolib.core.basemodel import SerializerConfig

class TimSerializer:
    @staticmethod
    def serialize(path: Path, data: Dict, config: SerializerConfig) -> None:
        """
        Serializes the timeseries data to the file at the specified path in .tim format.

        Attributes:
            path (Path): The path to the destination file.
            data (Dict): The data to be serialized.
            config (SerializerConfig): The serialization configuration.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

        space = 1 * " "
        format_float = lambda x: f"{x:{config.float_format}}"

        with path.open("w") as f:
            for time in data:
                series = space.join([format_float(p) for p in data[time]])
                timeserie = f"{format_float(time)}{space}{series}"
                f.write(f"{timeserie}\n")