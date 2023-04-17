from pathlib import Path
from typing import Callable, Dict, List

from pydantic.class_validators import validator

from hydrolib.core.basemodel import BaseModel, ModelSaveSettings, ParsableFileModel

from .parser import TimParser
from .serializer import TimSerializer, TimSerializerConfig


class TimRecord(BaseModel):
    """Single tim record, representing a time and a list of data."""

    time: float
    """float: Time of the time record."""

    data: List[float] = []
    """List[float]: Record of the time record."""


class TimModel(ParsableFileModel):
    """Class representing a tim (*.tim) file."""

    serializer_config = TimSerializerConfig()
    """TimSerializerConfig: The serialization configuration for the tim file."""

    comments: List[str] = []
    """List[str]: A list with the header comment of the tim file."""

    timeseries: List[TimRecord] = []
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
