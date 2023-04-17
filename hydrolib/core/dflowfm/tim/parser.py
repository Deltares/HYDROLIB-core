from pathlib import Path
from typing import Any, Dict, List, Tuple

TimData = Dict[str, List[str]]


class TimParser:
    """
    A parser for .tim files.
    Full line comments at the start of the file are supported. Comment lines start with either a `*` or a `#`.
    No other comments are supported.
    """

    @staticmethod
    def parse(filepath: Path) -> Dict[str, List[Any]]:
        """Parse a .tim file into a dictionary with comments and time series data.

        Args:
            filepath (Path): Path to the .tim file to be parsed.

        Returns:
            Dict[str, List[Any]]: A dictionary with keys "comments" and "timeseries".
            - "comments" represents comments found at the start of the file.
            - "timeseries" is a list of dictionaries with the key as "time" and values as "data".
                - "time" is a time as a string.
                - "data" is data as a list of strings.

        Raises:
            ValueError: If the file contains a comment that is not at the start of the file.
            ValueError: If the data of the timeseries is empty.
        """

        comments: List[str] = []
        timeseries: List[TimData] = []

        with filepath.open(encoding="utf8") as file:
            lines = file.readlines()
            comments, start_timeseries_index = TimParser._read_header_comments(lines)
            timeseries = TimParser._read_time_series_data(lines, start_timeseries_index)

        return {"comments": comments, "timeseries": timeseries}

    @staticmethod
    def _read_header_comments(lines: List[str]) -> Tuple[List[str], int]:
        """Read the header comments of the lines from the .tim file.
        The comments are only expected at the start of the .tim file.
        When a non comment line is encountered, all comments from the header will be retuned together with the start index of the timeseries data.

        Args:
            lines (List[str]): Lines from the the .tim file which is read.

        Returns:
            Tuple of List[str] and int, the List[str] contains the commenst from the header, the int is the start index of the timeseries.
        """
        comments: List[str] = []
        start_timeseries_index = 0
        for line_index in range(len(lines)):

            line = lines[line_index].strip()

            if len(line) == 0:
                comments.append(line)
                continue

            if line.startswith("#") or line.startswith("*"):
                comments.append(line[1:])
                continue

            start_timeseries_index = line_index
            break

        return comments, start_timeseries_index

    @staticmethod
    def _read_time_series_data(
        lines: List[str], start_timeseries_index: int
    ) -> List[TimData]:
        timeseries: List[TimData] = []
        for line_index in range(start_timeseries_index, len(lines)):
            line = lines[line_index].strip()

            if len(line) == 0:
                continue

            TimParser._raise_error_if_contains_comment(line, line_index + 1)

            time, *values = line.split()

            TimParser._raise_error_if_values_empty(values, line_index)

            timrecord = {"time": time, "data": values}
            timeseries.append(timrecord)

        return timeseries

    @staticmethod
    def _raise_error_if_contains_comment(line: str, line_index: int) -> None:
        if "#" in line or "*" in line:
            raise ValueError(
                f"Line {line_index}: comments are only supported at the start of the file, before the time series data."
            )

    @staticmethod
    def _raise_error_if_values_empty(values: List[str], line_index: int) -> None:
        if len(values) == 0:
            raise ValueError(f"Line {line_index}: Time series cannot be empty.")
