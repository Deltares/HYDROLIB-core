import re
from pathlib import Path
from typing import List

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
    Partial comments will have the line skipped.
    """

    @staticmethod
    def parse(filepath: Path) -> List[TimTimeData]:
        """Parse an .tim file into a List of TimTimeDatas.

        Args:
            filepath (Path): .tim file to be read.

        Returns:
            List: List of "TimTimeData".\n
            When file is empty returns an empty list.
        """
        timeseries = []
        with filepath.open() as file:
            for line in file.readlines():
                TimParser._read_line(line, timeseries)
        return timeseries

    @staticmethod
    def _read_line(line, timeseries: List[TimTimeData]):
        if TimParser._line_is_comment(line):
            timeseries.append(TimTimeData(comment=line))
            return

        time, *series = re.split(timpattern, line.strip())

        if TimParser._line_has_not_enough_information(series):
            return

        TimParser._add_valid_timeserie(time, series, timeseries)

    @staticmethod
    def _add_valid_timeserie(
        time: str, series: List[str], timeseries: List[TimTimeData]
    ):
        timeserie = TimParser._create_timeserie(time, series)

        if timeserie is None:
            return

        timeseries.append(timeserie)

    @staticmethod
    def _create_timeserie(time: str, series: List[str]):
        if TimParser._not_numeric(time):
            return

        listofvalues = []
        for value in series:
            if TimParser._not_numeric(value):
                return
            listofvalues.append(float(value))

        return TimTimeData(time=float(time), series=listofvalues)

    @staticmethod
    def _not_numeric(value: str):
        return not value.replace(",", "").replace(".", "").replace("-", "").isnumeric()

    @staticmethod
    def _line_is_comment(line: str):
        strippedline = line.lstrip()
        return strippedline.startswith("#") or strippedline.startswith("*")

    @staticmethod
    def _line_has_not_enough_information(line: List[str]):
        return len(line) < 1
