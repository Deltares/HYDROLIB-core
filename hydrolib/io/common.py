"""common.py defines common constructs of the io module.
"""

from hydrolib.core.basemodel import BaseModel
from typing import Optional, Tuple


class ParseMsg(BaseModel):
    """ParseMsg defines a single message indicating a significant parse event."""

    line: Tuple[int, int]
    column: Optional[Tuple[int, int]]
    reason: str
