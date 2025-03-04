from typing import List

from pydantic.v1 import Field

from hydrolib.core.basemodel import BaseModel, ParsableFileModel


class CmpRecord(BaseModel):
    """Single cmp record, representing a harmonic component with amplitude and phase."""

    period: float
    """float: of the period."""

    amplitude: float
    """float: of the harmonic amplitude."""

    phase: float
    """float: of the harmonic phase."""


class CmpModel(ParsableFileModel):
    """Class representing a cmp (*.cmp) file."""

    comments: List[str] = Field(default_factory=list)
    """List[str]: A list with the header comment of the tim file."""

    components: List[CmpRecord] = Field(default_factory=list)
    """List[CmpRecord]: A list containing the harmonic components."""
