from pathlib import Path
from typing import Dict

from hydrolib.core.basemodel import SerializerConfig


class Serializer:
    """Serializer class for serializing the forcing data of the `ExtOldModel` to file."""
    def serialize(path: Path, data: Dict, config: SerializerConfig):
        """Serializes the provided data to file at the specified path.

        Args: 
            path (Path): The path to write the data to.
            data (Dict): The data to be serialized.
            config (SerializerConfig): The config describing the serialization options. 
        """
        pass