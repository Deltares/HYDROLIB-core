import re
from pathlib import Path
from typing import Dict, List

timpattern = re.compile(r"\s+")

class TimTimeData:
    """
    TimTimeData provides a simple structurefor timeseries from the .tim file.
    """

    comment: str
    time: float
    series: List[float]

    def __init__(self, time=None, series=None, comment=None):
        """Initializes a new instance of the TimTimeData class.

        Args:
            time (float): Time linked to the series.
            series (List[float]): Series of values linked to the time.
            comment (str): comment line, when the line is a full comment.
        """
        self.time = time
        self.series = series
        self.comment = comment
        
class TimParser:
    """
    A parser for .tim files.
    Full line comments are supported.
    Partial comments will raise an error.
    """

    @staticmethod
    def parse(filepath: Path) -> dict():
        """Parse an .tim file into a dict.

        Args:
            filepath (Path): .tim file to be read.

        Returns:
            dict: dictionary with keys \"comment\" & time as numeric and value as List of floats".\n
            When file is empty returns an dictionary with only comment as key.
        """
        data: Dict = dict()
        data["comments"] = [str]
        with filepath.open() as file:
            for line in file.readlines():
                if TimParser._line_is_comment(line):
                    data["comments"].append(line.removeprefix('#').removeprefix('*'))
                    continue
                
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
