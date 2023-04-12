from pathlib import Path
from typing import Callable, Dict, List

from pydantic.class_validators import validator

from hydrolib.core.basemodel import ModelSaveSettings, ParsableFileModel

from .parser import TimParser
from .serializer import TimSerializer, TimSerializerConfig

from hydrolib.core.basemodel import BaseModel

class TimRecord(BaseModel):
    """Single time record, representing a time and a list of data.

    Attributes:
        time: time for which the data is used.
        data: values for the time.
    """
    time: float
    data: List[float]

class TimModel(ParsableFileModel):
    """Class representing a tim (*.tim) file."""

    serializer_config = TimSerializerConfig()
    """TimSerializerConfig: The serialization configuration for the tim file."""

    comments: List[str]
    """List[str]: A list with the header comment of the tim file."""

    timeseries: List[TimRecord]
    """List[TimRecord]: A list containing the time series as a TimRecord."""

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
    def _get_parser(cls) -> Callable:
        return TimParser.parse

    @validator("timeseries")
    @classmethod
    def _timeseries_values(
        cls, v: List[TimRecord]
    ) -> List[TimRecord]:
        """Validates if the amount of columns per timeseries match.

        Args:
            v (Dict[float, List[float]]): Value to validate, the timeseries in this case.

        Raises:
            ValueError: When the amount of columns differs per timeseries.

        Returns:
            Dict[float, List[float]: Validated timeseries.
        """
        if len(v) == 0:
            return v
        
        cls._raise_error_if_amount_of_columns_differ(v)
        cls._raise_error_if_duplicate_time(v)

        return v
    
    def _raise_error_if_amount_of_columns_differ(timeseries: List[TimRecord]):
        n_columns = len(timeseries[0].data)

        if n_columns == 0:
            raise ValueError("Time series cannot be empty.")

        for timrecord in timeseries:
            if len(timrecord.data) != n_columns:
                raise ValueError(
                    f"Time {timrecord.time}: Expected {n_columns} columns, but was {len(timrecord.data)}"
                )
    
    def _raise_error_if_duplicate_time(
        timeseries: List[TimRecord]
    ) -> None:
        seen_times = set()
        for timrecord in timeseries:
            if timrecord.time in seen_times:
                raise ValueError(
                f"Timeseries cannot contain duplicate times. Time: {timrecord.time} is duplicate."
            )
            seen_times.add(timrecord.time)
