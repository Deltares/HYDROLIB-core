from pathlib import Path
from typing import Callable, Dict, List

from pydantic.v1 import Field

from hydrolib.core.basemodel import BaseModel, ModelSaveSettings, ParsableFileModel
from hydrolib.core.dflowfm.cmp.parser import CmpParser
from hydrolib.core.dflowfm.cmp.serializer import CmpSerializer


class CmpRecord(BaseModel):
    """Single cmp record, representing a harmonic component with amplitude and phase."""

    period: float
    """float: of the period."""

    amplitude: float
    """float: of the amplitude."""

    phase: float
    """float: of the phase."""


class CmpModel(ParsableFileModel):
    """Class representing a cmp (*.cmp) file.

    Examples:
        Create a `CmpModel` object from a dictionary:
            ```python
            >>> data = {
            ...     "comments": ["# Example comment"],
            ...     "components": [CmpRecord(period=0.0, amplitude=1.0, phase=2.0)]
            ... }
            >>> cmp_model = CmpModel(**data)
            >>> print(cmp_model.components)
            [CmpRecord(period=0.0, amplitude=1.0, phase=2.0)]

            ```
    """

    comments: List[str] = Field(default_factory=list)
    """List[str]: A list with the header comment of the cmp file."""

    components: List[CmpRecord] = Field(default_factory=list)
    """List[CmpRecord]: A list containing the harmonic components."""

    @classmethod
    def _ext(cls) -> str:
        return ".cmp"

    @classmethod
    def _filename(cls) -> str:
        return "components"

    @classmethod
    def _get_serializer(
        cls,
    ) -> Callable[[Path, Dict, ModelSaveSettings], None]:
        return CmpSerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable[[Path], Dict]:
        return CmpParser.parse
