from hydrolib.core.basemodel import FileModel
from typing import List, Callable
from datetime import datetime
from .parser import BuiParser
from .serializer import BuiSerializer

class BuiModel(FileModel):
    default_dataset: int = 1 # Default value (always)
    number_of_stations: int
    name_of_stations: List[str]
    number_of_events: int
    observation_timestep: int
    first_recorded_event: datetime
    precipitation_per_timestep: List[float]

    @classmethod
    def _ext(cls) -> str:
        return ".bui"
    
    @classmethod
    def _get_serializer(cls) -> Callable:
        return BuiSerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable:
        return BuiParser.parse