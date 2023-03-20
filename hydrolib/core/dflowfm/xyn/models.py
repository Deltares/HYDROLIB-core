from typing import Optional

from hydrolib.core.basemodel import BaseModel


class XYNPoint(BaseModel):
    """Single XYN point.

    Attributes:
        x: x or λ coordinate
        y: y or φ coordinate
        n: name
    """

    x: float
    y: float
    n: str

    def _get_identifier(self, data: dict) -> Optional[str]:
        x = data.get("x")
        y = data.get("y")
        n = data.get("n")
        return f"x:{x} y:{y} n:{n}"
