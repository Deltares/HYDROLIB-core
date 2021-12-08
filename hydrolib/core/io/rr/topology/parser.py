from pathlib import Path
from warnings import warn

from hydrolib.core.utils import get_substring_between


class NetworkTopologyFileParser:
    """A parser for RR topology files such as node and link files."""

    def __init__(self, enclosing_tag: str):
        """Initializes a new instance of the `NetworkTopologyFileParser` class.

        Args:
            closing_tag (str): The enclosing tag for the enclosed topology data per record.
        """

        self.enclosing_tag = enclosing_tag

    def parse(self, path: Path) -> dict:
        """Parses a network topology file to a dictionary.

        Args:
            path (Path): Path to the network topology file.
        """

        if not path.is_file():
            warn(f"File: `{path}` not found, skipped parsing.")
            return {}

        with open(path) as file:
            lines = file.readlines()

        records = []

        key_start = self.enclosing_tag.upper()
        key_end = self.enclosing_tag.lower()

        for line in lines:

            substring = get_substring_between(line, key_start, key_end)
            if substring == None:
                continue

            parts = substring.split()

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

            records.append(record)

        return {key_end: records}
