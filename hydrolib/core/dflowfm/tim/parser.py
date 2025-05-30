from pathlib import Path
from typing import Any, Dict, List

from hydrolib.core.base.parser import BaseParser

TimData = Dict[str, List[str]]


class TimParser(BaseParser):
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
        with filepath.open(encoding="utf8") as file:
            lines = file.readlines()
            comments, start_timeseries_index = TimParser._read_header_comments(lines)
            timeseries = TimParser._read_time_series_data(lines, start_timeseries_index)

        return {"comments": comments, "timeseries": timeseries}

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
    def _raise_error_if_values_empty(values: List[str], line_index: int) -> None:
        if len(values) == 0:
            raise ValueError(f"Line {line_index}: Time series cannot be empty.")
