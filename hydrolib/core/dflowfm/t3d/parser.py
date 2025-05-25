"""T3D File Parser."""

from pathlib import Path
from typing import Any, Dict, List

from hydrolib.core.base.parser import BaseParser


class T3DParser(BaseParser):
    """
    A parser for .t3d files.
    Full line comments at the start of the file are supported. Comment lines start with either a `*` or a `#`.
    No other comments are supported.
    """

    @staticmethod
    def parse(filepath: Path) -> Dict[str, List[Any]]:
        """Parse a .t3d file into a dictionary with comments and parsed data from the t3d file.

        Args:
            filepath (Path): Path to the .t3d file to be parsed.

        Returns:
            Dict[str, List[Any]]: A dictionary with keys "records", "layers", and "layer_type".
            - "comments" represents comments found at the start of the file.
            - "layer_type": The type of the layer ["SIGMA", "Z"].
            - "layers": A list of floats representing the layers.
            - "records" is a list of dictionaries with the key as "time" and values as "data".
                - "time" is a time as a string.
                - "data" is data as a list of floats.

        Raises:
            ValueError: If the file contains a comment that is not at the start of the file.
            ValueError: If the data of the timeseries is empty.

        Examples:
            >>> from pathlib import Path
            >>> from hydrolib.core.dflowfm.t3d.parser import T3DParser
            >>> data = T3DParser.parse(Path("tests/data/input/dflowfm_individual_files/t3d/sigma-5-layers-3-times.t3d"))
            >>> print(data) # doctest: +SKIP
            {
                "comments": [],
                "layer_type": "SIGMA",
                "layers": [0.0, 0.2, 0.6, 0.8, 1.0],
                "records": [
                    {
                        "time": "0 seconds since 2006-01-01 00:00:00 +00:00",
                        "data": [1.0, 1.0, 1.0, 1.0, 1.0]
                    },
                    {
                        "time": "180 seconds since 2001-01-01 00:00:00 +00:00",
                        "data": [2.0, 2.0, 2.0, 2.0, 2.0]
                    },
                    {
                        "time": "9999999 seconds since 2001-01-01 00:00:00 +00:00",
                        "data": [3.0, 3.0, 3.0, 3.0, 3.0]
                    }
                ]
            }
        """
        with filepath.open(encoding="utf8") as file:
            lines = file.readlines()
            comments, start_timeseries_index = T3DParser._read_header_comments(lines)
            data = T3DParser._read_data(lines, start_timeseries_index)

        return {"comments": comments} | data

    @staticmethod
    def _read_data(
        lines: List[str], start_timeseries_index: int
    ) -> Dict[str, List[Any]]:
        parsed_data = {"records": []}
        i = start_timeseries_index

        while i < len(lines):
            line = lines[i].strip()

            if len(line) == 0:
                i += 1
                continue

            T3DParser._raise_error_if_contains_comment(line, i + 1)

            # 1. Detect LAYER_TYPE
            if line.startswith("LAYER_TYPE="):
                # everything after the '=' is the type (e.g., "SIGMA")
                parsed_data["layer_type"] = line.split("=", 1)[1].strip()

            # 2. Detect LAYERS
            elif line.startswith("LAYERS="):
                # everything after the '=' is a space-separated list of floats
                layer_str = line.split("=", 1)[1].strip()
                parsed_data["layers"] = [float(x) for x in layer_str.split()]

            # 3. Detect TIME + next line of data
            elif line.startswith("TIME"):
                # Grab everything after the '='
                time_value = line.split("=", 1)[1].strip()
                i += 1
                # The next line should contain the data
                data_line = lines[i]
                data_values = [float(x) for x in data_line.split()]
                # Save into the dictionary
                parsed_data["records"].append({"time": time_value, "data": data_values})

            i += 1

        return parsed_data
