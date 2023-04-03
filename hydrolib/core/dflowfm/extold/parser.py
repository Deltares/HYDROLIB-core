from pathlib import Path
from typing import Dict, List

from hydrolib.core.dflowfm.extold.common_io import ORDERED_FORCING_FIELDS


class Parser:
    """Parser class for parsing the forcing data of the old external forcings file to a dictionary to construct the `ExtOldModel` with."""

    @staticmethod
    def parse(filepath: Path) -> Dict:
        """Parses the file at the specified path to the forcing data.

        If a line starts with an asterisk (*) it is considered a comment and will not be parsed.

        Args:
            path (Path): The path to parse the data from.

        Returns:
            Dict[str, List[Dict[str, str]]]: A dictionary containing the forcing data under the key 'forcing'.
                                             The value is a list with dictionaries. Each dictionary represents a forcing block from the file.
        Raises:
            ValueError: Thrown when the order of a forcing block is not correct. Fields should be in the following order:
            "QUANTITY", "FILENAME", "VARNAME", "SOURCEMASK", "FILETYPE", "METHOD", "OPERAND", "VALUE", "FACTOR", "IFRCTYP",
            "AVERAGINGTYPE", "RELATIVESEARCHCELLSIZE", "EXTRAPOLTOL", "PERCENTILEMINMAX", "AREA", "NUMMIN"
        """

        forcings: List[Dict[str, str]] = []
        current_forcing: Dict[str, str] = {}

        with filepath.open() as file:
            for line_index, line in enumerate(file.readlines()):

                line = line.strip()
                if line.startswith("*"):
                    continue

                if len(line) == 0:
                    if len(current_forcing) != 0:
                        Parser._validate_order(current_forcing, line_index)
                        forcings.append(current_forcing)
                        current_forcing = {}
                    continue

                key, value = line.split("=", 1)
                current_forcing[key.strip()] = value.strip()

            if len(current_forcing) != 0:
                Parser._validate_order(current_forcing, line_index)
                forcings.append(current_forcing)

        return dict(forcing=forcings)

    @staticmethod
    def _validate_order(forcing: Dict[str, str], line_number: int):
        """Validates the order of the forcing fields given in the forcing block.

        - The fields are compared case insensitive.
        - For each KNOWN field that was parsed the order is checked.
        """

        parsed_fields_upper = [f.upper() for f in forcing.keys()]
        model_fields_upper = [f.upper() for f in ORDERED_FORCING_FIELDS]

        # Get the ordered KNOWN parsed fields, by filtering out unknown fields
        parsed_fields_ordered = [
            f for f in model_fields_upper if f in parsed_fields_upper
        ]

        # Get the unorderd KNOWN parsed fields, by filtering out unknown fields
        parsed_fields_unordered = [
            f for f in parsed_fields_upper if f in model_fields_upper
        ]

        if parsed_fields_unordered != parsed_fields_ordered:
            line_number_start = line_number + 1 - len(parsed_fields_upper)
            parsed_fields_ordered_str = ", ".join(parsed_fields_ordered)
            raise ValueError(
                f"Line {line_number_start}: Properties should be in the following order: {parsed_fields_ordered_str}"
            )
