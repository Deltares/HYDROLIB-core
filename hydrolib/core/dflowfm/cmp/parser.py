from pathlib import Path
from typing import Any, Dict, List

TimData = Dict[str, List[str]]


class CmpParser:
    """"""

    @staticmethod
    def parse(filepath: Path) -> Dict[str, List[Any]]:
        """Parse a cmp file to a Dict containing amplitude and phase for period."""
        with filepath.open(encoding="utf8") as file:
            lines = file.readlines()
            print(lines)
            # handle data
        comments = ""
        components = list([0, 1, 2], [1, 2, 3])
        return {"comments": comments, "components": components}
