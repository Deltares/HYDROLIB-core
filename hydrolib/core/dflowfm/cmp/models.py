from pathlib import Path
from typing import Callable, Dict, List

from pydantic.v1 import Field

from hydrolib.core.basemodel import BaseModel, ModelSaveSettings, ParsableFileModel
from hydrolib.core.dflowfm.cmp.astronomicname import AstronomicName
from hydrolib.core.dflowfm.cmp.parser import CmpParser
from hydrolib.core.dflowfm.cmp.serializer import CmpSerializer


class HarmonicRecord(BaseModel):
    """Single cmp record, representing a harmonic component with amplitude and phase."""

    period: float
    """float: of the period."""

    amplitude: float
    """float: of the amplitude."""

    phase: float
    """float: of the phase."""


class AstronomicRecord(BaseModel):
    """Single cmp record, representing an astronomic component with amplitude and phase."""

    name: AstronomicName
    """string of the astronomic name."""

    amplitude: float
    """float: of the amplitude."""

    phase: float
    """float: of the phase."""


class CmpRecord(BaseModel):
    harmonics: List[HarmonicRecord] = Field(default_factory=list)
    """List[HarmonicRecord]: A list containing the harmonic components."""

    astronomics: List[AstronomicRecord] = Field(default_factory=list)
    """List[AstronomicRecord]: A list containing the astronomic components."""


class CmpModel(ParsableFileModel):
    """Class representing a cmp (*.cmp) file.
    This class is used to parse and serialize cmp files, which contain
    information about various components such as harmonics and astronomics.

    Attributes:
        comments (List[str]): A list with the header comment of the cmp file.
        components (CmpRecord): A record with the components of the cmp file.

    Examples:
        Create a `CmpModel` object from a dictionary:
            ```python
            >>> data = {
            ...     "comments": ["# Example comment"],
            ...     "components": {
            ...         "harmonics": [{"period": 0.0, "amplitude": 1.0, "phase": 2.0}],
            ...         "astronomics": [{"name": "4MS10", "amplitude": 1.0, "phase": 2.0}]
            ...     }
            ... }
            >>> cmp_model = CmpModel(**data)
            >>> print(cmp_model.components.astronomics)
            [AstronomicRecord(name='4MS10', amplitude=1.0, phase=2.0)]

            ```
    See Also:
        CmpRecord: Class representing the components of the cmp file.
        CmpSerializer: Class responsible for serializing cmp files.
        CmpParser: Class responsible for parsing cmp files.
    """

    comments: List[str] = Field(default_factory=list)
    """List[str]: A list with the header comment of the cmp file."""

    components: CmpRecord = Field(default_factory=CmpRecord)
    """CmpRecord: A record with the components of the cmp file."""

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
