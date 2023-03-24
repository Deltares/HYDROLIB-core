from pathlib import Path
from typing import Dict, List


class Parser:
    """Parser class for parsing the forcing data of the old external forcings file to a dictionary to construct the `ExtOldModel` with."""

    @staticmethod
    def parse(filepath: Path, model_fields: List[str]) -> Dict:
        """Parses the file at the specified path to the forcing data.

        If a line starts with an asterisk (*) it is considered a comment and will not be parsed.

        Args:
            path (Path): The path to parse the data from.
            model_fields (List[str]): List of the  ordered model fields.

        Returns:
            Dict: A dictionary containing the forcing data under the key 'forcing'.
        """

        forcings = []
        current_forcing = {}

        with filepath.open() as file:
            for line_index, line in enumerate(file.readlines()):

                line = line.strip()
                if line.startswith("*"):
                    continue

                if len(line) == 0:
                    if len(current_forcing) != 0:
                        Parser.validate_order(current_forcing, model_fields, line_index) 
                        forcings.append(current_forcing)
                    current_forcing = {}
                    continue

                key, value = line.split("=", 1)
                current_forcing[key.strip()] = value.strip()

        return dict(forcing=forcings)
    
    @classmethod
    def validate_order(cls, forcing: dict, model_fields: List[str], line_number: int):
        parsed_fields_upper = [f.upper() for f in forcing.keys()]
        model_fields_upper = [f.upper() for f in model_fields]

        parsed_fields_ordered = [f for f in model_fields_upper if f in parsed_fields_upper]
        parsed_fields_unordered = [f for f in parsed_fields_upper if f in model_fields_upper] 

        if parsed_fields_unordered != parsed_fields_ordered:
            line_number_start = line_number - len(parsed_fields_upper) + 1
            parsed_fields_ordered_str = ", ".join(parsed_fields_ordered)
            raise ValueError(f"Line {line_number_start}: Properties should be in the following order: {parsed_fields_ordered_str}")
