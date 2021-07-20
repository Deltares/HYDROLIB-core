"""common.py defines common constructs of the io module.
"""

from pathlib import Path
from pydantic import BaseModel as PydanticBaseModel
from typing import Optional, Protocol, Tuple, Union


# TODO: Replace this BaseModel with the basemodel defined in basemodel.py once in main
class BaseModel(PydanticBaseModel):
    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True
        use_enum_values = True
        extra = "allow"


class ParseMsg(BaseModel):
    """ParseMsg defines a single message indicating a significant parse event."""

    line: Tuple[int, int]
    column: Optional[Tuple[int, int]]
    reason: str


class LineReader(Protocol):
    """FileReader describes the protocol to read lines from a file.

    The File object matches this protocol, and thus can be used as
    input for any function utilising the TextReader
    """

    def readline(self, size: int = -1) -> str:
        """Read until newline or EOF and return a single str.

        If the stream is already at EOF, an empty string is returned.

        Args:
            size (int, optional): Number of characters to read.
                                            Defaults to -1.

        Returns:
            str: A string consisting of the specified number of characters.
        """
