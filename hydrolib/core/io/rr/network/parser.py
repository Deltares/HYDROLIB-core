from pathlib import Path
from warnings import warn

from hydrolib.core.utils import get_list_index_safely


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

        key_start = "NODE"
        key_end = "node"

        length_parts = len(parts)

        index = 0
        while index < length_parts:

            index_startnode = get_list_index_safely(
                parts, key_start, index, length_parts
            )
            if index_startnode == -1:
                continue

            index_nextnode = get_list_index_safely(
                parts, key_start, index_startnode + 1, length_parts
            )
            if index_nextnode == -1:
                index_nextnode = length_parts

            index_endnode = get_list_index_safely(
                parts, key_end, index_startnode + 1, index_nextnode
            )
            if index_endnode == -1:
                index = index_nextnode
                continue

            index = index_startnode
            index += 1

            node = {}

            while index < index_endnode - 1:
                key = parts[index]
                if key == "mt" and parts[index + 1] == "1":
                    # `mt 1` is one keyword, but was parsed as two separate parts.
                    index += 1

                index += 1
                value = parts[index].strip("'")
                index += 1

                node[key] = value

            nodes.append(node)
            index += 1

        return dict(node=nodes)
