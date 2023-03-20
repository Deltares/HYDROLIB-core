import re
from pathlib import Path
from typing import List

timpattern = re.compile(r"\s+")

class TimTimeSerie():
    comment : str
    time : float
    serie : List[float]

    def __init__(self, time = None, series = None, comment = None):
        self.time = time
        self.series = series
        self.comment = comment

class TimParser:
    """
    A parser for .tim files which are like this:

    number number    number
    number number number # comment

    Note that the whitespace can vary and the comment
    left out.
    """

    @staticmethod
    def parse(filepath: Path) -> List[TimTimeSerie]:

        timeseries = []

        with filepath.open() as f:
            for line in f.readlines():
                
                if TimParser._line_is_comment(line):
                    timeseries.append(TimTimeSerie(comment=line))
                    continue

                time, *series = re.split(timpattern, line.strip())

                if TimParser._line_has_not_enough_information(series):
                    continue

                try:
                    listofvalues = []
                    for value in series :
                        listofvalues.append(float(value))
                
                    timeserie = TimTimeSerie(time=float(time), series=listofvalues)
                    timeseries.append(timeserie)
                except:
                    continue
                
        return timeseries
    
    @staticmethod
    def _line_is_comment(line:str):
        strippedline = line.lstrip() 
        return strippedline.startswith('#') or strippedline.startswith('*')
    
    @staticmethod
    def _line_has_not_enough_information(line:list[str]):
        return len(line) < 1
