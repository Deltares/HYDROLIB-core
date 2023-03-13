import re
from pathlib import Path
from typing import Dict

timpattern = re.compile(r"\s+")

class TimParser:
    """
    A parser for .tim files which are like this:

    number number    number
    number number number # comment

    Note that the whitespace can vary and the comment
    left out.
    """

    @staticmethod
    def parse(filepath: Path) -> Dict:

        timeseries: Dict = dict()

        with filepath.open() as f:
            for line in f.readlines():

                if TimParser._line_is_comment(line):
                    continue

                splitline = re.split(timpattern, line.lstrip().strip('\n'))

                if TimParser._line_has_not_enough_information(splitline):
                    continue

                try:
                    timeserie = TimParser._set_timeserie(splitline)
                    time = timeserie[0]
                    serie = timeserie[1]
                    timeseries[time] = serie
                except:
                    continue
                
        return timeseries
    
    @staticmethod
    def _line_is_comment(line:str):
        return line.lstrip().startswith('#') or line.lstrip().startswith('*')
    
    @staticmethod
    def _line_has_not_enough_information(line:str):
        return len(line) < 2
    
    @staticmethod
    def _set_timeserie(timeserie:list):
        time = float(timeserie[0])
        series = timeserie
        series.remove(timeserie[0])

        listofvalues = []
        for value in series :
            listofvalues.append(float(value))

        return [time, listofvalues]