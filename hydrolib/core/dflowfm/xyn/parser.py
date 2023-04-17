from pathlib import Path
from typing import Dict


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
            Dict[str, List[XYNPoint]]: dictionary with "points" value set to a list of points
                each of which is a dict itself, with keys 'x', 'y', and 'n'.

        Raises:
            ValueError: if a line in the file cannot be parsed
                or if the name contains whitespace while not surrounded with
                single or double quotes.
        """

        def is_surrounded_by_single_quotes(name: str) -> bool:
            return name.startswith("'") and name.endswith("'")

        def is_surrounded_by_double_quotes(name: str) -> bool:
            return name.startswith('"') and name.endswith('"')

        def is_surrounded_by_quotes(name: str) -> bool:
            return is_surrounded_by_single_quotes(
                name
            ) or is_surrounded_by_double_quotes(name)

        def may_contain_whitespace(name: str) -> bool:
            return is_surrounded_by_quotes(name)

        def contains_whitespace(name: str) -> bool:
            return " " in name

        def contains_whitespace_while_not_allowed(name: str) -> bool:
            return not may_contain_whitespace(name) and contains_whitespace(name)

        points = []

        with filepath.open(encoding="utf8") as f:
            for linenr, line in enumerate(f.readlines()):

                line = line.strip()
                if line.startswith("*") or len(line) == 0:
                    continue

                try:
                    x, y, n = line.split(maxsplit=2)
                except ValueError:
                    raise ValueError(
                        f"Error parsing XYN file '{filepath}', line {linenr+1}."
                    )

                if contains_whitespace_while_not_allowed(n):
                    raise ValueError(
                        f"Error parsing XYN file '{filepath}', line {linenr+1}. Name `{n}` contains whitespace, so should be enclosed in quotes."
                    )

                if is_surrounded_by_quotes(n):
                    n = n[1:-1]

                points.append(dict(x=x, y=y, n=n))

        return dict(points=points)
