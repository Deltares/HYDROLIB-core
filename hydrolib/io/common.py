"""common.py defines common constructs of the io module.
"""

from enum import Enum
from pydantic import BaseModel as PydanticBaseModel
from typing import Tuple


# TODO: Replace this BaseModel with the basemodel defined in basemodel.py once in main
class BaseModel(PydanticBaseModel):
    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True
        use_enum_values = True
        extra = "allow"


class ParseErrorLevel(Enum):
    """ParseErrorLevel defines the possible error levels of ParseMsg objects.

    - FATAL indicates we could not recover from the error, and no result will be
      returned.
    - ERROR indicates the integrity of the data is compromised, however we can
      continue to read data.
    - WARNING indicates an unexpected event, however the integrity of the data
      is ensured.
    - INFO indicates some event that does not necessarily require user intervention.
    """
    FATAL = 0
    ERROR = 1
    WARNING = 2
    INFO = 3


class ParseMsg(BaseModel):
    """ParseMsg defines a single message indicating a significant parse event.
    """
    level: ParseErrorLevel
    line: Tuple[int, int]
    column: Tuple[int, int]
    reason: str