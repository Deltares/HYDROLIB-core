from pathlib import Path
from typing import Any, Dict, List, Tuple

CmpData = Dict[str, Tuple[int, int, int]]


class CmpParser:
    """"""

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
                ...    cmp_model = CmpParser.parse(Path(""))
                >>> print(cmp_model)
                {'comments': ['some comment'], 'components': [{'period': '0.0', 'amplitude': '1.0', 'phase': '2.0'}]}
        """
        with filepath.open(encoding="utf8") as file:
            lines = file.readlines()
            comments, start_components_index = CmpParser._read_header_comments(lines)
            components = CmpParser._read_components_data(lines, start_components_index)
        return {"comments": comments, "components": components}

    @staticmethod
    def _read_header_comments(lines: List[str]) -> Tuple[List[str], int]:
        """Read the header comments of the lines from the .cpm file.
        The comments are only expected at the start of the .cpm file.
        When a non comment line is encountered, all comments from the header will be retuned together with the start index of the components data.

        Args:
            lines (List[str]): Lines from the the .cpm file.

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
    ) -> List[CmpData]:
        components_data: List[CmpData] = []
        for line_index in range(start_components_index, len(lines)):
            line = lines[line_index].strip()

            if len(line) == 0:
                continue

            CmpParser._raise_error_if_contains_comment(line, line_index + 1)

            period, amplitude, phase = filter(None, line.split(" "))

            component = {"period": period, "amplitude": amplitude, "phase": phase}
            components_data.append(component)

        return components_data

    @staticmethod
    def _raise_error_if_contains_comment(line: str, line_index: int) -> None:
        if "#" in line or "*" in line:
            raise ValueError(
                f"Line {line_index}: comments are only supported at the start of the file, before the components data."
            )
