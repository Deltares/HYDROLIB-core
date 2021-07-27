from io import TextIOWrapper
from pathlib import Path
from typing import Dict, List, Tuple


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

            for line in DIMRSerializer._serialize(data, 2):
                # tuple with indentation level and text
                f.write(line[0] * " " + line[1] + "\n")

            f.write("</dimrConfig>")

    @staticmethod
    def _serialize(data: Dict, indent: int):
        for key in data:
            value = data[key]
            if isinstance(value, Dict):
                yield from DIMRSerializer._serialize_dict(key, value, indent)
            elif isinstance(value, List):
                for item in value:
                    yield from DIMRSerializer._serialize_dict(key, item, indent)
            else:
                yield (indent, f"<{key}>{value}</{key}>")

    @staticmethod
    def _serialize_dict(key: str, data: Dict, indent: int):
        name = data.pop("name", None)

        if name:
            if len(data) == 0:
                yield (indent, f'<{key} name="{name}" />')
                return

            yield (indent, f'<{key} name="{name}">')
        else:
            yield (indent, f"<{key}>")

        yield from DIMRSerializer._serialize(data, indent + 2)

        yield (indent, f"</{key}>")
