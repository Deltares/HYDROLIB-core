from pathlib import Path
from warnings import warn

from hydrolib.core.utils import get_list_index_safely


class NetworkTopologyFileParser:
    """A parser for topology files such as node and link files."""

    def __init__(self, enclosing_tag: str):
        """Initializes a new instance of the `NetworkTopologyFileParser` class.

        Args:
            closing_tag (str): The enclosing tag for the enclosed topology data per item.
        """

        self.enclosing_tag = enclosing_tag

    def parse(self, path: Path):
        """Parses a network topology file to a dictionary.

        Args:
            path (Path): Path to the network topology file.
        """

        if not path.is_file():
            warn(f"File: `{path}` not found, skipped parsing.")
            return {}

        with open(path) as file:
            parts = file.read().split()

        records = []

        key_start = self.enclosing_tag.upper()
        key_end = self.enclosing_tag.lower()

        length_parts = len(parts)

        index = 0
        while index < length_parts:

            index_startrecord = get_list_index_safely(
                parts, key_start, index, length_parts
            )
            if index_startrecord == -1:
                continue

            index_nextrecord = get_list_index_safely(
                parts, key_start, index_startrecord + 1, length_parts
            )
            if index_nextrecord == -1:
                index_nextrecord = length_parts

            index_endrecord = get_list_index_safely(
                parts, key_end, index_startrecord + 1, index_nextrecord
            )
            if index_endrecord == -1:
                index = index_nextrecord
                continue

            index = index_startrecord
            index += 1

            record = {}

            while index < index_endrecord - 1:
                key = parts[index]
                if key == "mt" and parts[index + 1] == "1":
                    # `mt 1` is one keyword, but was parsed as two separate parts.
                    index += 1

                index += 1
                value = parts[index].strip("'")
                index += 1

                record[key] = value

            records.append(record)
            index += 1

        return {key_end: records}
