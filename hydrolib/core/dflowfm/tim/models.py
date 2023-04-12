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
        cls, v: Dict[float, List[float]]
    ) -> Dict[float, List[float]]:
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

        timeseries_iterator = iter(v.items())
        _, columns = next(timeseries_iterator)
        n_columns = len(columns)

        if n_columns == 0:
            raise ValueError("Time series cannot be empty.")

        for time, values in timeseries_iterator:
            if len(values) != n_columns:
                raise ValueError(
                    f"Time {time}: Expected {n_columns} columns, but was {len(values)}"
                )

        return v
