from pathlib import Path
from warnings import warn

from hydrolib.core.basemodel import BaseModel, FileModel


class NodeFileParser:
    """A parser for topology node files."""

    @staticmethod
    def parse(path: Path):
        """Parses a topology node file to a dictionary.

        Args:
            path (Path): Path to the topology node file.
        """

        if not path.is_file():
            warn(f"File: `{path}` not found, skipped parsing.")
            return {}

        with open(path) as file:
            parts = file.read().split()

        nodes = []

        begin = "NODE"
        end = "node"

        index = 0
        while index < len(parts):

            if parts[index] != begin:
                index += 1
                continue

            index += 1
            dict = {}

            while parts[index] != end and index < len(parts) - 1:
                key = parts[index]
                if key == "mt" and parts[index + 1] == "1":
                    # `mt 1` is one keyword, but was parsed as two separate parts.
                    index += 1

                index += 1
                value = parts[index]
                index += 1

                dict[key] = value

            if parts[index] == end:
                nodes.append(dict)

        return {"node": nodes}
