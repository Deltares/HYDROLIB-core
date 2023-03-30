import re
from pathlib import Path
from typing import Dict

timpattern = re.compile(r"\s+")


class TimParser:
    """
    A parser for .tim files.
    Full line comments at the start of the file are supported by * and #.
    No other comments are supported.
    """

    @staticmethod
    def parse(filepath: Path) -> Dict:
        """Parse an .tim file into a dict.

        Args:
            filepath (Path): .tim file to be read.

        Returns:
            dict: dictionary with keys \"comment\" & time as numeric and value as List of floats".\n
            When file is empty returns an dictionary with only comment as key.
        """
        data = {}
        data["comments"] = [str]
        savecomments = True
        with filepath.open() as file:
            for line in file.readlines():
                if TimParser._line_is_comment(line):
                    if savecomments:
                        data["comments"].append(line.lstrip("#*"))
                        continue
                    raise ValueError(f"Error parsing tim file '{filepath}', comments in between data not supported.")
                
                savecomments = False

                try:
                    TimParser._add_timeseries(line, data)

                except ValueError:
                    raise ValueError(f"Error parsing tim file '{filepath}'.")

        return data

    @staticmethod
    def _add_timeseries(line, data):
        time, *series = re.split(timpattern, line.strip())

        if TimParser._line_has_not_enough_information(series):
            raise (ValueError("Not enough information in line."))
        listofvalues = []

        for value in series:
            if TimParser._not_numeric(value):
                raise (ValueError("No numeric data detected."))
            listofvalues.append(float(value))

        data[float(time)] = listofvalues

    @staticmethod
    def _not_numeric(value: str):
        return not value.replace(",", "").replace(".", "").replace("-", "").isnumeric()

    @staticmethod
    def _line_is_comment(line: str):
        strippedline = line.lstrip()
        return strippedline.startswith("#") or strippedline.startswith("*")

    @staticmethod
    def _line_has_not_enough_information(line):
        return len(line) < 1
