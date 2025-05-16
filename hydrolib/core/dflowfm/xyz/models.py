from pathlib import Path
from typing import Callable, Dict, List, Optional

from pydantic import Field

from hydrolib.core.basemodel import (
    BaseModel,
    ModelSaveSettings,
    ParsableFileModel,
    SerializerConfig,
)

from .parser import XYZParser
from .serializer import XYZSerializer


class XYZPoint(BaseModel):
    """Single sample or forcing point.

    Attributes:
        x: x or λ coordinate
        y: y or φ coordinate
        z: sample value or group number (forcing)
        comment: keyword for grouping (forcing)
    """

    x: float
    y: float
    z: float
    comment: Optional[str] = Field(
        None, alias="group", description="comment or group name"
    )

    def _get_identifier(self, data: dict) -> Optional[str]:
        x = data.get("x")
        y = data.get("y")
        z = data.get("z")
        return f"x:{x} y:{y} z:{z}"


class XYZModel(ParsableFileModel):
    """Sample or forcing file.

    Attributes:
        points: List of [`XYZPoint`][hydrolib.core.dflowfm.xyz.models.XYZPoint]
    """

    points: List[XYZPoint] = []

    def dict(self, *args, **kwargs):
        # speed up serializing by not converting these lowest models to dict
        return dict(points=self.points)

    @classmethod
    def _ext(cls) -> str:
        return ".xyz"

    @classmethod
    def _filename(cls) -> str:
        return "sample"

    @classmethod
    def _get_serializer(
        cls,
    ) -> Callable[[Path, Dict, SerializerConfig, ModelSaveSettings], None]:
        return XYZSerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable[[Path], Dict]:
        return XYZParser.parse
