from pathlib import Path
from typing import Callable, Dict, List

from pydantic.v1 import Field
from pydantic.v1.class_validators import validator

from hydrolib.core.basemodel import BaseModel, ModelSaveSettings, ParsableFileModel
from hydrolib.core.dflowfm.tim.parser import TimParser
from hydrolib.core.dflowfm.tim.serializer import TimSerializer, TimSerializerConfig


class TimRecord(BaseModel):
    """Single tim record, representing a time and a list of data."""

    time: float
    """float: Time of the time record."""

    data: List[float] = Field(default_factory=list)
    """List[float]: Record of the time record."""


class TimModel(ParsableFileModel):
    """Class representing a tim (*.tim) file.

    Attributes:
    -----------
    serializer_config : TimSerializerConfig
        Configuration for serialization of the .tim file.
    comments : List[str]
        Header comments from the .tim file.
    timeseries : List[TimRecord]
        A list of TimRecord objects, each containing a time value and associated data.

    Methods:
    --------
    _ext() -> str
        Returns the file extension for .tim files.
    _filename() -> str
        Returns the default filename for .tim files.
    _get_serializer() -> Callable
        Returns the serializer callable for .tim files.
    _get_parser() -> Callable
        Returns the parser callable for .tim files.
    _validate_timeseries_values(cls, v: List[TimRecord]) -> List[TimRecord]
        Validates the timeseries data.

    Args:
    -----
    filepath : Path
        Path to the .tim file.
    data : Dict
        Parsed data containing comments and timeseries.
    serializer_config : TimSerializerConfig
        Configuration for serializing the .tim file.

    Returns:
    --------
    List[TimRecord]
        Validated list of TimRecord objects.

    Raises:
    -------
    ValueError
        If the timeseries has inconsistent column counts or duplicate time values.

    Examples:
    ---------
    Create a TimModel object from a .tim file:
        >>> from hydrolib.core.dflowfm.tim.models import TimModel, TimRecord
        >>> tim_model = TimModel(filepath="tests/data/input/tim/triple_data_for_timeseries.tim")
        >>> print(tim_model.timeseries)
        [TimRecord(time=10.0, data=[1.232, 2.343, 3.454]), TimRecord(time=20.0, data=[4.565, 5.676, 6.787]), TimRecord(time=30.0, data=[1.5, 2.6, 3.7])]

    Create `TimModel` from `TimRecord` objects:
        >>> new_tim = TimModel()
        >>> new_tim.comments = ["# Example comment"]
        >>> new_tim.timeseries = [TimRecord(time=0.0, data=[1.0, 2.0])]

    Serialize the `TimModel` to a .tim file:
        >>> new_tim.save(filepath="output.tim") # doctest: +SKIP

    See Also:
    ---------
    TimParser
        Used for parsing .tim files.
    TimSerializer
        Used for serializing .tim files.
    TimRecord
        Represents individual time and data entries in the timeseries.

    Notes:
    ------
    This class ensures the integrity of the timeseries by validating data consistency and detecting duplicate time entries.

    References:
        - `TIM file format <https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#C4>`_
    """

    serializer_config = TimSerializerConfig()
    """TimSerializerConfig: The serialization configuration for the tim file."""

    comments: List[str] = Field(default_factory=list)
    """List[str]: A list with the header comment of the tim file."""

    timeseries: List[TimRecord] = Field(default_factory=list)
    """List[TimRecord]: A list containing the timeseries."""

    @classmethod
    def _ext(cls) -> str:
        return ".tim"

    @classmethod
    def _filename(cls) -> str:
        return "timeseries"

    @classmethod
    def _get_serializer(
        cls,
    ) -> Callable[[Path, Dict, TimSerializerConfig, ModelSaveSettings], None]:
        return TimSerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable[[Path], Dict]:
        return TimParser.parse

    @validator("timeseries")
    @classmethod
    def _validate_timeseries_values(cls, v: List[TimRecord]) -> List[TimRecord]:
        """Validate if the amount of columns per timeseries match and if the timeseries have no duplicate times.

        Args:
            v (List[TimRecord]): Timeseries to validate.

        Raises:
            ValueError: When the amount of columns for timeseries is zero.
            ValueError: When the amount of columns differs per timeseries.
            ValueError: When the timeseries has a duplicate time.

        Returns:
            List[TimRecord]: Validated timeseries.
        """
        if len(v) == 0:
            return v

        cls._raise_error_if_amount_of_columns_differ(v)
        cls._raise_error_if_duplicate_time(v)

        return v

    @staticmethod
    def _raise_error_if_amount_of_columns_differ(timeseries: List[TimRecord]) -> None:
        n_columns = len(timeseries[0].data)

        if n_columns == 0:
            raise ValueError("Time series cannot be empty.")

        for timrecord in timeseries:
            if len(timrecord.data) != n_columns:
                raise ValueError(
                    f"Time {timrecord.time}: Expected {n_columns} columns, but was {len(timrecord.data)}"
                )

    @staticmethod
    def _raise_error_if_duplicate_time(timeseries: List[TimRecord]) -> None:
        seen_times = set()
        for timrecord in timeseries:
            if timrecord.time in seen_times:
                raise ValueError(
                    f"Timeseries cannot contain duplicate times. Time: {timrecord.time} is duplicate."
                )
            seen_times.add(timrecord.time)
