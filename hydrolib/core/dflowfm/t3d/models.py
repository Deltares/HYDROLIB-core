"""T3D file"""

import re
from typing import List

from pydantic.v1 import Field, validator
from strenum import StrEnum

from hydrolib.core.basemodel import BaseModel


class LayerType(StrEnum):
    """
    Layer types in the t3d file.
    """

    sigma = "SIGMA"
    z = "Z"


TIME_PATTERN = re.compile(
    r"^"
    r"(\d+(?:\.\d+)?(?:[eE][+\-]?\d+)?)\s+"  # (1) sci_float = \d+(?:\.\d+)?(?:[eE][+\-]?\d+)?  (handles 1, 1.23, 1e9, 1.23e-10, etc.)
    r"(seconds|minutes|hours|days)\s+"  # (2) space + valid time unit
    r"since\s+"  # (3) space + 'since' + space
    r"\d{4}-\d{2}-\d{2}"  # (4) date in YYYY-MM-DD e.g. 2006-01-01
    r"(?:[T ][0-9]{2}:[0-9]{2}:[0-9]{2})?"  # (5) optional time: preceded by 'T' or space, then hh:mm:ss 'T00:00:00' or ' 00:00:00'
    r"(?:\s*(?:Z|[+\-][0-9]{2}:[0-9]{2}))?"  # (6)(7) optional whitespace + optional timezone: Z or ±hh:mm
    r"$"
)


class T3DTimeRecord(BaseModel):
    """Single tim record, representing a time and a list of data.

    Args:
        time (str):
            A time string of the format: '<float> <time unit> since <ISO date> [optional time] [optional timezone]'.
            Example: '15.5 seconds since 2023-02-01T13:45:59Z'
            - the time unit is [seconds|minutes|hours|days].
            - ISO date YYYY-MM-DD.
            - With optional time and optional timezone.
            - i.e, "15.5 seconds since 2023-02-01T13:45:59Z"

        data (List[float]):
            Record of the time record.

    Raises:
        ValueError: If the time string is not in the expected format.

    Examples:
        ```python
        >>> record = T3DTimeRecord(time="15.5 seconds since 2023-02-01T13:45:59Z", data=[1, 2, 3, 4, 5])
        >>> record
        T3DTimeRecord(time='15.5 seconds since 2023-02-01T13:45:59Z', data=[1.0, 2.0, 3.0, 4.0, 5.0])

        ```
    """

    time: str = Field(
        ...,
        description=(
            "A time string of the format: '<float> <time unit> since <ISO date> [optional time] [optional timezone]'. "
            "Example: '15.5 seconds since 2023-02-01T13:45:59Z'"
        ),
    )

    data: List[float] = Field(default_factory=list)

    @validator("time", pre=True, check_fields=True, allow_reuse=True)
    def validate_time_format(cls, value: str) -> str:
        """Check if the time string is in the expected format.

        - YYYY-MM-DD
        - Optional time, e.g. T12:34:56 or  12:34:56
        - Optional timezone: Z or +hh:mm or -hh:mm
        """
        if not TIME_PATTERN.match(value):
            raise ValueError(
                f"Time string '{value}' is not in the expected format:\n"
                "    <float> <time unit> since <ISO date> [optional time] [optional timezone]"
            )
        return value
