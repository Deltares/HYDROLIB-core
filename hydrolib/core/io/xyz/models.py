from typing import Optional
from hydrolib.core.basemodel import BaseModel
from pydantic import Field


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
