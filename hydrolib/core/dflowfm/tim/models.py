from pathlib import Path
from typing import Callable, Dict, List

from hydrolib.core.basemodel import ModelSaveSettings, ParsableFileModel

from .parser import TimParser
from .serializer import TimSerializer, TimSerializerConfig

from pydantic.class_validators import validator

class TimModel(ParsableFileModel):
    """Class representing a tim (*.tim) file.

    Attributes:
        data: Dictionary with keys \"comment\" & time as float and value as List of floats".\n
        serializer_config: TimSerializerConfig

    Raises:
        ValueError: If the time and values are not parsable to float, or when the amount of columns differs per timeseries.
    """

    serializer_config = TimSerializerConfig()

    comments : List[str]
    timeseries: Dict[float, List[float]]

    @classmethod
    def _ext(cls) -> str:
        return ".tim"

    @classmethod
    def _filename(cls) -> str:
        return "sample"

    @classmethod
    def _get_serializer(
        cls,
    ) -> Callable[[Path, Dict, TimSerializerConfig, ModelSaveSettings], None]:
        return TimSerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable:
        return TimParser.parse
    
    @validator('timeseries')
    @classmethod
    def _timeseries_values(cls, v: Dict[float, List[float]]) -> Dict[float, List[float]]:
        """Validates if the amount of columns per timeseries match.

        Args:
            v (Dict[float, List[float]]): Value to validate, the timeseries in this case.

        Raises:
            ValueError: If the time and values are not parsable to float, or when the amount of columns differs per timeseries.

        Returns:
            Dict[float, List[float]: Validated timeseries.
        """
        firstlengthset = False
        for time in v:
            if not firstlengthset:
                length = len(v[time])
                firstlengthset = True
                continue

            if length != len(v[time]):
                raise ValueError(f"Problem with values in timeseries, for time {time}")
            length = len(v[time])
            
        return v
