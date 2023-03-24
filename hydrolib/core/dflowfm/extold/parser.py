from pathlib import Path
from typing import Dict


class Parser:
    """Parser class for parsing the forcing data of the old external forcings file to a dictionary to construct the `ExtOldModel` with."""

    @staticmethod
    def parse(filepath: Path) -> Dict:
        """Parses the file at the specified path to the forcing data.

        If a line starts with an asterisk (*) is it considered a comment and will not be parsed.

        Args:
            path (Path): The path to parse the data from.

        Returns:
            Dict: A dictionary containing the forcing data under the key 'forcing'.
        """
        data: Dict = dict(forcing=[])

        return data
