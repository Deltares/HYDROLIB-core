from pathlib import Path
from typing import Dict, List

from hydrolib.core.dflowfm.extold.common_io import ORDERED_FORCING_FIELDS


class Parser:
    """Parser class for parsing the forcing data of the old external forcings file to a dictionary to construct the `ExtOldModel` with."""

    @staticmethod
    def parse(filepath: Path) -> Dict:
        """Parses the file at the specified path to the forcing data.

        If a line starts with an asterisk (*) it is considered a comment.
        Comments are only allowed at the header of the file. Elsewhere, they will be skipped.

        Args:
            path (Path): The path to parse the data from.

        Returns:
            Dict[str, List[Any]]: A dictionary with the parsed data, with two keys:
                - 'comment' (List[str]): A list of the parsed comments.
                - 'forcing' (List[Dict[str, str]]): A list of the parsed forcing data as dictionaries. Each dictionary represents a forcing block from the file, with the parsed key value pairs.

        Raises:
            ValueError: Thrown when the order of a forcing block is not correct. Fields should be in the following order:
            "QUANTITY", "FILENAME", "VARNAME", "SOURCEMASK", "FILETYPE", "METHOD", "OPERAND", "VALUE", "FACTOR", "IFRCTYP",
            "AVERAGINGTYPE", "RELATIVESEARCHCELLSIZE", "EXTRAPOLTOL", "PERCENTILEMINMAX", "AREA", "NUMMIN"
        """

        with filepath.open(encoding="utf8") as file:
            lines = file.readlines()

        comments, start_data_index = Parser._parse_header(lines)
        forcings = Parser._parse_data(lines, start_data_index)

        return dict(comment=comments, forcing=forcings)

    @staticmethod
    def _parse_header(lines: List[str]):
        comments: List[str] = []

        start_data_index = 0
        for line_index in range(len(lines)):

            line = lines[line_index].strip()

            if len(line) == 0:
                comments.append(line)
                continue

            if line.startswith("*"):
                comments.append(line[1:])
                continue

            start_data_index = line_index
            break

        return comments, start_data_index

    @staticmethod
    def _parse_data(lines: List[str], start_index: int):
        forcings: List[Dict[str, str]] = []
        current_forcing: Dict[str, str] = {}

        for line_index in range(start_index, len(lines)):

            line = lines[line_index].strip()

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

        return forcings

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
