from pathlib import Path
from typing import Callable, Dict, List, Optional

from pydantic.v1 import validator

from hydrolib.core.base.models import (
    BaseModel,
    ModelSaveSettings,
    ParsableFileModel,
    SerializerConfig,
)
from hydrolib.core.base.utils import str_is_empty_or_none

from .parser import XYNParser
from .serializer import XYNSerializer


class XYNPoint(BaseModel):
    """Single XYN point, representing a named station location."""

    x: float
    """float: The x or λ coordinate."""

    y: float
    """float: The y or φ coordinate."""

    n: str
    """float: The name of the point."""

    def _get_identifier(self, data: dict) -> Optional[str]:
        x = data.get("x")
        y = data.get("y")
        n = data.get("n")
        return f"x:{x} y:{y} n:{n}"

    @validator("n", pre=True)
    def _validate_name(cls, value):
        if str_is_empty_or_none(value):
            raise ValueError("Name cannot be empty.")

        if "'" in value or '"' in value:
            raise ValueError(
                "Name cannot contain single or double quotes except at the start and end."
            )

        return value


class XYNModel(ParsableFileModel):
    """Observation station (.xyn) file."""

    points: List[XYNPoint] = []
    """List[`XYNPoint`]: List of XYN points."""

    def dict(self, *args, **kwargs):
        # speed up serializing by not converting these lowest models to dict
        return dict(points=self.points)

    @classmethod
    def _filename(cls) -> str:
        return "stations_obs"

    @classmethod
    def _ext(cls) -> str:
        return ".xyn"

    @classmethod
    def _get_serializer(
        cls,
    ) -> Callable[[Path, Dict, SerializerConfig, ModelSaveSettings], None]:
        return XYNSerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable[[Path], Dict]:
        return XYNParser.parse
