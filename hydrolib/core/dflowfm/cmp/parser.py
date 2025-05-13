from pathlib import Path
from typing import Any, Dict, List, Tuple

from hydrolib.core.baseparser import BaseParser

AstronomicData = Dict[str, Tuple[float, float, float]]
HarmonicData = Dict[str, Tuple[str, float, float]]
CMPData = Dict[str, Tuple[AstronomicData, HarmonicData]]


class CMPParser(BaseParser):
    """Parser for .cmp files.
    Full line comments at the start of the file are supported. Comment lines start with either a `*` or a `#`.
    No other comments are supported.
    """

    @staticmethod
    def parse(filepath: Path) -> Dict[str, List[Any]]:
        r"""Parse a cmp file to a Dict containing amplitude and phase for period.

        Args:
            filepath (Path): Path to the .cmp file to be parsed.

        Returns:
            Dict[str, List[Any]]: A dictionary with keys "comments" and "components".
            - "comments" represents comments found at the start of the file.
            - "components" is a list of dictionaries with the values "period", "amplitude" and "phase".
                - "period" is a float as a string.
                - "amplitude" is a float as a string.
                - "phase" is a float as a string.

        Raises:
            ValueError: If the file contains a comment that is not at the start of the file.

        Examples:
            Read a `.cmp` file:
                ```python
                >>> file_path = Path(
                ...    "tests/data/input/e02/f006_external_forcing/c020_basinnofriction_squares/openboundary1_0001.cmp"
                ... )
                >>> cmp_model = CMPParser.parse(file_path)
                >>> print(cmp_model)  # doctest: +ELLIPSIS
                {'comments': [' COLUMNN=3', ' COLUMN1=Period (min) or Astronomical Componentname',... 'amplitude': '1.0000000', 'phase': '45.1200000'}]}}

                ```
        """
        with filepath.open(encoding="utf8") as file:
            lines = file.readlines()
            comments, start_components_index = CMPParser._read_header_comments(lines)
            component = CMPParser._read_components_data(lines, start_components_index)
        return {"comments": comments, "component": component}

    @staticmethod
    def _read_components_data(
        lines: List[str], start_components_index: int
    ) -> List[CMPData]:
        harmonics_data: List[CMPData] = []
        astronomics_data: List[CMPData] = []
        for line_index in range(start_components_index, len(lines)):
            line = lines[line_index].strip()

            if len(line) == 0:
                continue

            CMPParser._raise_error_if_contains_comment(line, line_index + 1)

            period, amplitude, phase = line.split()

            if CMPParser._is_float(period):
                component = {"period": period, "amplitude": amplitude, "phase": phase}
                harmonics_data.append(component)
            else:
                component = {"name": period, "amplitude": amplitude, "phase": phase}
                astronomics_data.append(component)

        component_data = {}
        if harmonics_data:
            component_data["harmonics"] = harmonics_data
        if astronomics_data:
            component_data["astronomics"] = astronomics_data

        return component_data

    @staticmethod
    def _is_float(element: any) -> bool:
        if element is None:
            return False
        try:
            float(element)
            return True
        except ValueError:
            return False

    @staticmethod
    def _raise_error_if_contains_comment(line: str, line_index: int) -> None:
        if "#" in line or "*" in line:
            raise ValueError(
                f"Line {line_index}: comments are only supported at the start of the file, before the components data."
            )
