from pathlib import Path
from warnings import warn

from hydrolib.core.utils import get_substring_between


class NodeFileParser:
    """A parser for topology node files."""

    @staticmethod
    def parse(path: Path) -> dict:
        """Parses a topology node file to a dictionary.

        Args:
            path (Path): Path to the topology node file.
        """

        if not path.is_file():
            warn(f"File: `{path}` not found, skipped parsing.")
            return {}

        with open(path) as file:
            lines = file.readlines()

        nodes = []

        key_start = "NODE"
        key_end = "node"

        for line in lines:

            substring = get_substring_between(line, key_start, key_end)
            if substring == None:
                continue

            parts = substring.split()
            length_parts = len(parts)

            node = {}

            index = 0
            while index < length_parts - 1:
                key = parts[index]
                if key == "mt" and parts[index + 1] == "1":
                    # `mt 1` is one keyword, but was parsed as two separate parts.
                    index += 1

                index += 1
                value = parts[index].strip("'")
                index += 1

                node[key] = value

            nodes.append(node)

        return dict(node=nodes)
