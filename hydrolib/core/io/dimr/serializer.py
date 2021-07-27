from io import TextIOWrapper
from pathlib import Path
from typing import Dict, List


class DIMRSerializer:
    def serialize(path: Path, data: Dict):
        """
        Serializes the DIMR data to the file at the specified path.

        Attributes:
            path (Path): The path to the destination file.
            data (Dict): The data to be serialized.
        """

        path.parent.mkdir(parents=True, exist_ok=True)

        with path.open("w") as f:
            f.write('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')
            f.write(
                '<dimrConfig xmlns="http://schemas.deltares.nl/dimr" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://schemas.deltares.nl/dimr http://content.oss.deltares.nl/schemas/dimr-1.3.xsd">\n'
            )

            DIMRSerializer._serialize_data(f, data, 2)

            f.write("</dimrConfig>\n")

    @staticmethod
    def _serialize_data(f: TextIOWrapper, data: Dict, indent: int):
        for key in data:
            value = data[key]
            if isinstance(value, Dict):
                DIMRSerializer._serialize_dict(f, key, value, indent)
            elif isinstance(value, List):
                for item in value:
                    DIMRSerializer._serialize_dict(f, key, item, indent)
            else:
                f.write(indent * " " + f"<{key}>{value}</{key}>\n")

    @staticmethod
    def _serialize_dict(f: TextIOWrapper, key: str, data: Dict, indent: int):
        name = data.pop("name", None)
        if name:
            f.write(indent * " " + f'<{key} name="{name}">\n')
        else:
            f.write(indent * " " + f"<{key}>\n")

        DIMRSerializer._serialize_data(f, data, indent + 2)

        f.write(indent * " " + f"</{key}>\n")
