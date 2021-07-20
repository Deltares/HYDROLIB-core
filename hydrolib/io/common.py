"""common.py defines common constructs of the io module.
"""

from enum import Enum
from pydantic import BaseModel as PydanticBaseModel
from typing import Optional, Tuple


# TODO: Replace this BaseModel with the basemodel defined in basemodel.py once in main
class BaseModel(PydanticBaseModel):
    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True
        use_enum_values = True
        extra = "allow"


class ParseMsg(BaseModel):
    """ParseMsg defines a single message indicating a significant parse event.
    """
    line: Tuple[int, int]
    column: Optional[Tuple[int, int]]
    reason: str