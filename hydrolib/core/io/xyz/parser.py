import re
from pathlib import Path
from typing import Dict

xyzpattern = re.compile(r"\s+")


class XYZParser:
    """
    A parser for .xyz files which are like this:

    number number    number
    number number number # comment

    Note that the whitespace can vary and the comment
    left out.
    """

    @staticmethod
    def parse(filepath: Path) -> Dict:

        data: Dict = dict(points=[])

        with filepath.open() as f:
            for line in f.readlines():

                if len(line) < 5:  # 3 values, two whitespaces
                    continue

                x, y, z, c = re.split(xyzpattern, line, maxsplit=3)

                c = c.strip("#").strip()
                if len(c) == 0:
                    c = None

                data["points"].append(dict(x=x, y=y, z=z, comment=c))

        return data
