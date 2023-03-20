from pathlib import Path
from typing import Callable, Dict, List

from hydrolib.core.basemodel import ParsableFileModel, SerializerConfig

from .parser import TimParser
from .serializer import TimSerializer, TimSerializerConfig, TimTimeSerie


class TimModel(ParsableFileModel):
    """Model or tim data.

    Attributes:
        timeseries: List[TimTimeSerie]
    """

    serializer_config = TimSerializerConfig()
    timeseries: List[TimTimeSerie]

    def dict(self, *args, **kwargs):
        # speed up serializing by not converting these lowest models to dict
        return self.timeseries

    @classmethod
    def _ext(cls) -> str:
        return ".tim"

    @classmethod
    def _filename(cls) -> str:
        return "sample"

    @classmethod
    def _get_serializer(cls) -> Callable[[Path, Dict, TimSerializerConfig], None]:
        return TimSerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable:
        return TimParser.parse
