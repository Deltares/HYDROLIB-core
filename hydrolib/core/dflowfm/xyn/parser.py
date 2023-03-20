import re
from pathlib import Path
from typing import Dict
from .name_extrator import NameExtractor

xynpattern = re.compile(r"\s+")


class XYNParser:
    """
    A parser for .xyn files with contents like this:

    number number id

    Note that the amount of whitespace can vary.
    """

    @staticmethod
    def parse(filepath: Path) -> Dict:
        """Parse an .xyn file into a Dict with the list of points read.

        Args:
            filepath (Path): .xyn file to be read.

        Returns:
            Dict: dictionary with "points" value set to a list of points
                each of which is a dict itself, with keys 'x', 'y', and 'n'.

        Raises:
            ValueError: if a line in the file contains no values that
                could be parsed.
        """
        data: Dict = dict(points=[])

        with filepath.open() as f:
            for linenr, line in enumerate(f.readlines()):

                line = line.strip()
                if line.startswith("*") or len(line) == 0:
                    continue

                try:
                    x, y, remainder = re.split(xynpattern, line, maxsplit=2)
                    n = NameExtractor.extract_name(remainder)
                except ValueError:
                    raise ValueError(
                        f"Error parsing XYN file '{filepath}', line {linenr+1}."
                    )

                data["points"].append(dict(x=x, y=y, n=n))

        return data
