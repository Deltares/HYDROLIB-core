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
        """Parse an .xyz file into a Dict with the list of points read.

        Args:
            filepath (Path): .xyz file to be read.

        Returns:
            Dict: dictionary with "points" value set to a list of points
                each of which is a dict itself, with keys 'x', 'y', 'z'
                and 'c' for an optional comment.

        Raises:
            ValueError: if a line in the file contains no values that
                could be parsed.
        """

        data: Dict = dict(points=[])

        with filepath.open(encoding="utf8") as f:
            for linenr, line in enumerate(f.readlines()):

                line = line.strip()
                if line.startswith("*") or len(line) == 0:
                    continue

                try:
                    x, y, z, *c = re.split(xyzpattern, line, maxsplit=3)
                except ValueError:
                    raise ValueError(
                        f"Error parsing XYZ file '{filepath}', line {linenr+1}."
                    )

                c = c[0] if len(c) > 0 else ""
                c = c.strip("#").strip()
                if len(c) == 0:
                    c = None

                data["points"].append(dict(x=x, y=y, z=z, comment=c))

        return data
