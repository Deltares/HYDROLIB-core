import re
from pathlib import Path
from typing import List

timpattern = re.compile(r"\s+")


class TimTimeSerie:
    comment: str
    time: float
    serie: List[float]

    def __init__(self, time=None, series=None, comment=None):
        self.time = time
        self.series = series
        self.comment = comment


class TimParser:
    """
    A parser for .tim files which are like this:

    #comment
    number number number
    number number number

    Note that the whitespace can vary and the comment
    left out.
    """

    @staticmethod
    def parse(filepath: Path) -> List[TimTimeSerie]:
        timeseries = []
        with filepath.open() as file:
            for line in file.readlines():
                TimParser._read_line(line, timeseries)
        return timeseries

    @staticmethod
    def _read_line(line, timeseries):
        if TimParser._line_is_comment(line):
            timeseries.append(TimTimeSerie(comment=line))
            return

        time, *series = re.split(timpattern, line.strip())

        if TimParser._line_has_not_enough_information(series):
            return

        TimParser._add_valid_timeserie(time, series, timeseries)

    @staticmethod
    def _add_valid_timeserie(time, series, timeseries):
        try:
            timeserie = TimParser._create_timeserie(time, series)
            timeseries.append(timeserie)
            return
        except:
            return

    @staticmethod
    def _create_timeserie(time, series) -> TimTimeSerie:
        listofvalues = []
        for value in series:
            listofvalues.append(float(value))

        return TimTimeSerie(time=float(time), series=listofvalues)

    @staticmethod
    def _line_is_comment(line: str):
        strippedline = line.lstrip()
        return strippedline.startswith("#") or strippedline.startswith("*")

    @staticmethod
    def _line_has_not_enough_information(line: List[str]):
        return len(line) < 1
