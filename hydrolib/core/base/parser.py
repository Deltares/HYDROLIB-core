import logging
from pathlib import Path
from typing import Dict, List, Tuple

logger = logging.getLogger(__name__)

_FALLBACK_ENCODINGS = ("utf-8", "latin-1")


def open_file_with_fallback_encoding(filepath: Path) -> str:
    """Read a file trying UTF-8 first, then falling back to Latin-1.

    D-Flow FM model files may contain non-UTF-8 characters (e.g. the degree
    symbol ``°`` encoded as 0xB0 in Latin-1/Windows-1252).  This helper
    attempts UTF-8 first and, on failure, retries with Latin-1 which can
    decode any byte value in 0x00–0xFF.

    Args:
        filepath: Path to the file to read.

    Returns:
        The file content as a string.

    Raises:
        UnicodeDecodeError: If the file cannot be decoded with any of the
            attempted encodings (should not happen because Latin-1 accepts
            every byte).
    """
    for encoding in _FALLBACK_ENCODINGS:
        try:
            return filepath.read_text(encoding=encoding)
        except UnicodeDecodeError:
            logger.debug(
                f"Failed to decode {filepath} with {encoding}, trying next encoding.",
            )

    raise AssertionError("All fallback encodings failed.")  # pragma: no cover


class BaseParser:
    @staticmethod
    def _read_header_comments(lines: List[str]) -> Tuple[List[str], int]:
        """Read the header comments of the lines from the file.
        The comments are only expected at the start of the file.
        When a non comment line is encountered, all comments from the header will be retuned together with the start index of the data.

        Args:
            lines (List[str]): Lines from the the file which is read.

        Returns:
            Tuple of List[str] and int, the List[str] contains the commenst from the header, the int is the start index of the data.
        """
        comments: List[str] = []
        start_timeseries_index = 0
        for line_index, line in enumerate(lines):

            line = line.strip()

            if len(line) == 0:
                comments.append(line)
                continue

            if line.startswith("#") or line.startswith("*"):
                comments.append(line[1:])
                continue

            start_timeseries_index = line_index
            break

        return comments, start_timeseries_index

    @staticmethod
    def _raise_error_if_contains_comment(line: str, line_index: int) -> None:
        if "#" in line or "*" in line:
            raise ValueError(
                f"Line {line_index}: comments are only supported at the start of the file, before the data."
            )


class DummmyParser:
    @staticmethod
    def parse(filepath: Path) -> Dict:
        return {}
