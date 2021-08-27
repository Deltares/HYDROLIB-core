"""parser.py defines the read method for the RainfallRunoffModel."""

from typing import Dict, Iterable, Optional

from pydantic.types import FilePath


def _strip(lines: Iterable[str]) -> Iterable[str]:
    return (l.strip() for l in lines)


def _is_empty(line: str) -> bool:
    return len(line) == 0


def _is_comment(line: str) -> bool:
    return line[0] == "*"


def _to_path(line: str) -> Optional[str]:
    value = line.split("*", 1)[0].strip()[1:-1].strip()

    if len(value) == 0 or value == "not used":
        return None

    return value


def _to_values(lines: Iterable[str]) -> Iterable[Optional[str]]:
    return (_to_path(v) for v in _strip(lines) if not (_is_empty(v) or _is_comment(v)))


def parse(keys: Iterable[str], lines: Iterable[str]) -> Dict:
    """Parse the set of lines to its corresponding RainfallRunoffModel.

    Args:
        keys (Iterable[str]): The property keys of the RainfallRunoffModel.
        lines (Iterable[str]): The content of a file in .fnm format.

    Returns:
        RainfallRunoffModel: The corresponding RainfallRunoffModel.
    """
    values = _to_values(lines)
    return dict(zip(keys, values))


def read(keys: Iterable[str], path: FilePath) -> Dict:
    """Parse the file at the specified path into a RainfallRunoffModel

    Args:
        keys (Iterable[str]): The property keys of the RainfallRunoffModel.
        path (FilePath): The path to the Rainfall Runoff definition file

    Returns:
        RainfallRunoffModel: The RainfallRunoffModel corresponding with the file.
    """
    with path.open("r") as f:
        return parse(keys, f)
