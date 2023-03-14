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

                time, *series = re.split(timpattern, line.strip())

                if TimParser._line_has_not_enough_information(series):
                    continue

                try:
                    listofvalues = []
                    for value in series :
                        listofvalues.append(float(value))
                    
                    timeseries[float(time)] = listofvalues
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
