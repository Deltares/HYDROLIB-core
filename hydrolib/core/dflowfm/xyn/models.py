from pathlib import Path
from typing import Callable, Dict, List, Optional

from pydantic import validator

from hydrolib.core.basemodel import (
    BaseModel,
    ModelSaveSettings,
    ParsableFileModel,
    SerializerConfig,
)
from hydrolib.core.dflowfm.xyn.name_validator import NameValidator

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
        return NameValidator.validate(value)


class XYNModel(ParsableFileModel):
    """Observation station (.xyn) file.

    Attributes:
        points: List of [`XYNPoint`][hydrolib.core.dflowfm.xyn.models.XYNPoint]
    """

    points: List[XYNPoint] = []

    def dict(self, *args, **kwargs):
        # speed up serializing by not converting these lowest models to dict
        return dict(points=self.points)

    @classmethod
    def _ext(cls) -> str:
        return ".xyn"

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
