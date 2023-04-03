from pathlib import Path
from typing import Any, Dict, List

class TimParser:
    """A parser for .tim files that extracts comments and time series data."""

    @staticmethod
    def parse(filepath: Path) -> Dict[str, Any]:
        """Parse a .tim file into a dictionary with comments and time series data.

        Args:
            filepath (Path): Path to the .tim file to be read.

        Returns:
            Dict[str, Any]: A dictionary with keys "comments" and "timeseries", where "comments"
                  is a list of strings representing comments found at the start of the file, and
                  "timeseries" is a dictionary where each key is a time and each value
                  is a list of strings.

        Raises:
            ValueError: If the file contains a comment that is not at the start of the file or
             if the time series contains a duplicate time entry.
        """

        comments: List[str] = []
        timeseries: Dict[str, List[str]] = {}

        with filepath.open() as file:
            lines = file.readlines()

            # Read header comments
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

            # Read time series data
            for line_index in range(start_timeseries_index, len(lines)):
                line = lines[line_index].strip()

                if len(line) == 0:
                    continue

                TimParser._raise_error_if_contains_comment(line, line_index + 1)

                time, *values = line.split()

                TimParser._raise_error_if_duplicate_time(time, timeseries, line_index + 1)

                timeseries[time] = values

        return {"comments" : comments, "timeseries" : timeseries}

    @staticmethod
    def _raise_error_if_contains_comment(line: str, line_index: int):
        if "#" in line or "*" in line:
            raise ValueError(f"Line {line_index}: comments are only supported at the start of the file, before the time series data.")
    
    @staticmethod
    def _raise_error_if_duplicate_time(time: str, timeseries: Dict[str, List[str]], line_index: int):
        if time in timeseries:
            raise ValueError(f"Line {line_index}: time series cannot contain duplicate times. Time: {time}")