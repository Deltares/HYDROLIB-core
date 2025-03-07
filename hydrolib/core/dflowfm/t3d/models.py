"""T3D file"""

import re
from pathlib import Path
from typing import Callable, Dict, List, Optional

from pydantic.v1 import Field, validator
from strenum import StrEnum

from hydrolib.core.basemodel import (
    BaseModel,
    ModelSaveSettings,
    ParsableFileModel,
    SerializerConfig,
)
from hydrolib.core.dflowfm.t3d.parser import T3DParser
from hydrolib.core.dflowfm.t3d.serializer import T3DSerializer


class LayerType(StrEnum):
    """
    Layer types in the t3d file.
    """

    sigma = "SIGMA"
    z = "Z"


# Group1 (float at the beginning)
# Group2 (time unit) seconds|minutes|hours|days
# Group3 (date) YYYY-MM-DD
TIME_PATTERN = re.compile(
    r"^"
    r"(\d+(?:\.\d+)?(?:[eE][+\-]?\d+)?)\s+"  # (1) sci_float = \d+(?:\.\d+)?(?:[eE][+\-]?\d+)?  (handles 1, 1.23, 1e9, 1.23e-10, etc.)
    r"(seconds|minutes|hours|days)\s+"  # (2) space + valid time unit
    r"since\s+"  # (3) space + 'since' + space
    r"(\d{4}-\d{2}-\d{2}"  # (4) date in YYYY-MM-DD e.g. 2006-01-01 (|<---the parentheses at the beginning)
    r"(?:[T ][0-9]{2}:[0-9]{2}:[0-9]{2})?"  # (5) optional time: preceded by 'T' or space, then hh:mm:ss 'T00:00:00' or ' 00:00:00'
    r"(?:\s*(?:Z|[+\-][0-9]{2}:[0-9]{2}))?)"  # (6)(7) optional whitespace + optional timezone: Z or ±hh:mm. (|<---the parentheses ends here)
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


class T3DModel(ParsableFileModel):
    """T3D file model.

    Args:
        comments (List[str]):
            A list with the header comment of the tim file.

        records (List[T3DTimeRecord]):
            List of time records.

        layers (List[float]):
            List of layers.

        vectormax (Optional[int]):
            The VECTORMAX value.

        layer_type (LayerType):
            The layer type.

    Examples:
        >>> from hydrolib.core.dflowfm.t3d.models import T3DTimeRecord, T3DModel
        >>> layer_name = "SIGMA"
        >>> comments = ["comment1", "comment2"]
        >>> layers = [1, 2, 3, 4, 5]
        >>> record = [
        ...     T3DTimeRecord(time="0 seconds since 2006-01-01 00:00:00 +00:00", data=[5.0, 5.0, 10.0, 10.0]),
        ...     T3DTimeRecord(time="1e9 seconds since 2001-01-01 00:00:00 +00:00", data=[5.0, 5.0, 10.0, 10.0])
        ... ]
        >>> model = T3DModel(comments=comments, layer_type=layer_name, layers=layers, records=record)
        >>> print(model) # doctest: +SKIP
        T3DModel(
            filepath=None,
            serializer_config=SerializerConfig(float_format=''),
            comments=['comment1', 'comment2'],
            records=[
                T3DTimeRecord(time='0 seconds since 2006-01-01 00:00:00 +00:00', data=[5.0, 5.0, 10.0, 10.0]),
                T3DTimeRecord(time='1e9 seconds since 2001-01-01 00:00:00 +00:00', data=[5.0, 5.0, 10.0, 10.0])
            ],
            layers=[1.0, 2.0, 3.0, 4.0, 5.0], vectormax=1, layer_type='SIGMA'
        )

    """

    comments: List[str] = Field(default_factory=list)
    """List[str]: A list with the header comment of the tim file."""

    records: List[T3DTimeRecord] = Field(default_factory=list)

    layers: List[float] = Field(default_factory=list)
    vectormax: Optional[int] = Field(default=1, alias="VECTORMAX")
    layer_type: LayerType = Field(default=None, alias="LAYER_TYPE")

    def _ext(self) -> str:
        return ".t3d"

    def _filename(self) -> str:
        return "t3d"

    @classmethod
    def _get_parser(cls) -> Callable[[Path], Dict]:
        return T3DParser.parse

    @classmethod
    def _get_serializer(
        cls,
    ) -> Callable[[Path, Dict, SerializerConfig, ModelSaveSettings], None]:
        return T3DSerializer.serialize
