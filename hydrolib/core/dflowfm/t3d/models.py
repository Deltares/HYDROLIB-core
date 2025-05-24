"""T3D file"""

import re
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from pydantic.v1 import Field, root_validator, validator
from strenum import StrEnum

from hydrolib.core.base.models import (
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

    @property
    def time_unit(self) -> str:
        """Return the unit of the time string.

        Returns:
            str: The unit of the time string. The unit can be [seconds|minutes|hours|days].
        """
        match = TIME_PATTERN.match(self.time)
        return match.group(2)

    @property
    def reference_date(self) -> str:
        """Return the date of the time string.

        Returns:
            str: The date of the time string in the format: YYYY-MM-DD.
            - ISO date YYYY-MM-DD.
            - With optional time and optional timezone.
            - i.e, "15.5 seconds since 2023-02-01T13:45:59Z"
        """
        match = TIME_PATTERN.match(self.time)
        return match.group(3)

    @property
    def time_offset(self) -> float:
        """Return the time offset of the time string."""
        match = TIME_PATTERN.match(self.time)
        return float(match.group(1))


class T3DModel(ParsableFileModel):
    r"""T3D file model.

    Args:
        comments (List[str]):
            A list with the header comment of the tim file.
        records (List[T3DTimeRecord]):
            List of time records.
        layers (List[float]):
            List of layers.
        vectormax (Optional[int]):
            The VECTORMAX value. Default is None.
        layer_type (LayerType):
            The layer type.
        quantities_names (Optional[List[str]]):
            List of names for the quantities in the timeseries.

    Examples:
        ```python
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
            layers=[1.0, 2.0, 3.0, 4.0, 5.0], vectormax=None, layer_type='SIGMA', quantities_names=None
        )
        >>> print(model.size)
        (2, 4)
        >>> model.quantities_names = ["quantity-1", "quantity-2", "quantity-3"] # doctest: +SKIP
        Traceback (most recent call last):
            model.quantities_names = ["quantity-1", "quantity-2", "quantity-3"]
            ^^^^^^^^^^^^^^^^^^^^^^
          File "...\Lib\site-packages\pydantic\v1\main.py", line 397, in __setattr__
            raise ValidationError(errors, self.__class__)
        pydantic.v1.error_wrappers.ValidationError: 1 validation error for T3DModel
        __root__
          The number of quantities names must be equal to the number of values in the records. (type=value_error)
        >>> model.quantities_names = ["quantity-1", "quantity-2", "quantity-3", "quantity-4"]
        >>> print(model.quantities_names)
        ['quantity-1', 'quantity-2', 'quantity-3', 'quantity-4']

    ```
    """

    comments: List[str] = Field(default_factory=list)
    records: List[T3DTimeRecord] = Field(default_factory=list)
    layers: List[float] = Field(default_factory=list)
    vectormax: Optional[int] = Field(default=None, alias="VECTORMAX")
    layer_type: LayerType = Field(default=None, alias="LAYER_TYPE")
    quantities_names: Optional[List[str]] = Field(default=None)

    @validator("records", pre=False, check_fields=True, allow_reuse=True)
    def validate_record_length(cls, value: List[T3DTimeRecord]):
        """Check if the records have the same length."""
        records = [v.data for v in value]
        if not all(len(sublist) == len(records[0]) for sublist in records):
            raise ValueError("All records must have the same length.")

        return value

    @root_validator(pre=False)
    def validate_quantities_names(cls, value: Dict[str, str]) -> Dict[str, str]:
        """
        Validate that the number of quantities names is equal to the number of values in the records.
        """
        record = value.get("records")
        record_len = len(record[0].data)
        quantities_names = value.get("quantities_names")
        if quantities_names is not None and len(quantities_names) != record_len:
            raise ValueError(
                "The number of quantities names must be equal to the number of values in the records."
            )
        return value

    @property
    def size(self) -> Tuple[int, int]:
        """Return the number ot time step * length of each record."""
        return len(self.records), len(self.records[0].data)

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

    def as_dict(self) -> Dict[str, List[float]]:
        """Return the data from the records as a dictionary.

        Returns:
            data (Dict[str, List[float]]):
                A dictionary with the data from the records.

        Examples:
            ```python
            >>> from hydrolib.core.dflowfm.t3d.models import T3DTimeRecord, T3DModel
            >>> layer_name = "SIGMA"
            >>> comments = ["comment1", "comment2"]
            >>> layers = [0, 0.2, 0.6, 0.8, 1.0]
            >>> record = [
            ...     T3DTimeRecord(time="0 seconds since 2006-01-01 00:00:00 +00:00", data=[5.0, 5.0, 10.0, 10.0]),
            ...     T3DTimeRecord(time="1e9 seconds since 2001-01-01 00:00:00 +00:00", data=[5.0, 5.0, 10.0, 10.0])
            ... ]
            >>> model = T3DModel(comments=comments, layer_type=layer_name, layers=layers, records=record)
            >>> model.as_dict()
            {0.0: [5.0, 5.0, 10.0, 10.0], 1000000000.0: [5.0, 5.0, 10.0, 10.0]}

            ```
        """
        data = {}
        for record in self.records:
            match = TIME_PATTERN.match(record.time)
            offset_str, _, _ = match.groups()
            offset = float(offset_str)
            data[offset] = record.data

        return data

    def get_units(self):
        """Return the units for each quantity in the timeseries.

        Returns:
            List[str]: A list of units for each quantity in the timeseries.

        Examples:
            Create a `TimModel` object from a .tim file:
                ```python
                >>> from hydrolib.core.dflowfm.t3d.models import T3DTimeRecord, T3DModel
                >>> layer_name = "SIGMA"
                >>> comments = ["comment1", "comment2"]
                >>> layers = [0, 0.2, 0.6, 0.8, 1.0]
                >>> record = [
                ...     T3DTimeRecord(time="0 seconds since 2006-01-01 00:00:00 +00:00", data=[5.0, 5.0, 10, 10, 10]),
                ...     T3DTimeRecord(time="1e9 seconds since 2001-01-01 00:00:00 +00:00", data=[5.0, 5.0, 10, 10, 10])
                ... ]
                >>> model = T3DModel(comments=comments, layer_type=layer_name, layers=layers, records=record)
                >>> model.quantities_names = ["discharge", "waterlevel", "temperature", "salinity", "initialtracer"]
                >>> print(model.get_units())
                ['m3/s', 'm', 'degC', '1e-3', '-']

                ```
        """
        if self.quantities_names is None:
            return None
        return T3DModel._get_quantity_unit(self.quantities_names)
