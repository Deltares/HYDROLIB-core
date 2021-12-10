from pathlib import Path
from typing import Iterable
from warnings import warn

from hydrolib.core.utils import get_substring_between


class NetworkTopologyFileParser:
    """A parser for RR topology files such as node and link files."""

    def __init__(self, enclosing_tag: str):
        """Initializes a new instance of the `NetworkTopologyFileParser` class.

        Args:
            enclosing_tag (str): The enclosing tag for the enclosed topology data per record.
        """

        self._enclosing_tag = enclosing_tag

    def parse(self, path: Path) -> dict:
        """Parses a network topology file to a dictionary.

        Args:
            path (Path): Path to the network topology file.
        """

        file_content = self._read_file(path)
        return self._parse_lines(file_content)

    def _read_file(self, path: Path) -> Iterable[str]:
        if not path.is_file():
            warn(f"File: `{path}` not found, skipped parsing.")
            return []

        with open(path) as file:
            lines = file.readlines()
        return lines

    def _parse_lines(self, lines: Iterable[str]) -> dict:
        records = []

        key_start = self._enclosing_tag.upper()
        key_end = self._enclosing_tag.lower()

        for line in lines:

            substring = get_substring_between(line, key_start, key_end)
            if substring == None:
                continue

            record = self._parse_line(substring)
            records.append(record)

        return {key_end: records}

    def _parse_line(self, line: str) -> dict:
        parts = line.split()

        record = {}

        index = 0
        while index < len(parts) - 1:
            key = parts[index]
            if key == "mt" and parts[index + 1] == "1":
                # `mt 1` is one keyword, but was parsed as two separate parts.
                index += 1

            index += 1
            value = parts[index].strip("'")
            index += 1

            record[key] = value

        return record
