from pathlib import Path
from typing import Any, Dict, List, Tuple

AstronomicData = Dict[str, Tuple[float, float, float]]
HarmonicData = Dict[str, Tuple[str, float, float]]
CMPData = Dict[str, Tuple[AstronomicData, HarmonicData]]


class CMPParser:
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
                >>> import io
                >>> from unittest.mock import patch
                >>> file = io.StringIO("#some comment\n0.0   1.0  2.0")
                >>> with patch.object(Path, 'open') as mock_file:
                ...    mock_file.return_value = file
                ...    cmp_model = CMPParser.parse(Path(""))
                >>> print(cmp_model)
                {'comments': ['some comment'], 'component': {'harmonics': [{'period': '0.0', 'amplitude': '1.0', 'phase': '2.0'}]}}

                ```
        """
        with filepath.open(encoding="utf8") as file:
            lines = file.readlines()
            comments, start_components_index = CMPParser._read_header_comments(lines)
            component = CMPParser._read_components_data(lines, start_components_index)
        return {"comments": comments, "component": component}

    @staticmethod
    def _read_header_comments(lines: List[str]) -> Tuple[List[str], int]:
        """Read the header comments of the lines from the .cmp file.
        The comments are only expected at the start of the .cmp file.
        When a non comment line is encountered, all comments from the header will be retuned together with the start index of the components data.

        Args:
            lines (List[str]): Lines from the the .cmp file.

        Returns:
            Tuple of List[str] and int, the List[str] contains the comments from the header, the int is the start index of the components.
        """
        comments: List[str] = []
        start_components_index = 0
        for line_index in range(len(lines)):

            line = lines[line_index].strip()

            if len(line) == 0:
                comments.append(line)
                continue

            if line.startswith("#") or line.startswith("*"):
                comments.append(line[1:])
                continue

            start_components_index = line_index
            break

        return comments, start_components_index

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
