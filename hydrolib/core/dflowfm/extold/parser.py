from pathlib import Path
from typing import Dict


class Parser:
    """Parser class for parsing the forcing data of the old external forcings file to a dictionary to construct the `ExtOldModel` with."""

    @staticmethod
    def parse(filepath: Path) -> Dict:
        """Parses the file at the specified path to the forcing data.

        If a line starts with an asterisk (*) it is considered a comment and will not be parsed.

        Args:
            path (Path): The path to parse the data from.

        Returns:
            Dict: A dictionary containing the forcing data under the key 'forcing'.
        """

        forcings = []
        current_forcing = {}

        with filepath.open() as file:
            for line in file:

                line = line.strip()
                if line.startswith("*"):
                    continue

                if len(line) == 0:
                    if len(current_forcing) != 0:
                        forcings.append(current_forcing)
                    current_forcing = {}
                    continue

                key, value = line.split("=", 1)
                current_forcing[key.strip()] = value.strip()

        return dict(forcing=forcings)
