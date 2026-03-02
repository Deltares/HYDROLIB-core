"""models.py defines all classes and functions related to representing substance files."""

from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from pydantic import Field, field_validator
from strenum import StrEnum

from hydrolib.core.base.models import (
    BaseModel,
    ModelSaveSettings,
    ParsableFileModel,
    SerializerConfig,
)
from hydrolib.core.base.utils import FortranUtils
from hydrolib.core.dflowfm.substance.parser import SubstanceParser
from hydrolib.core.dflowfm.substance.serializer import (
    SubstanceSerializer,
    SubstanceSerializerConfig,
)


class SubstanceType(StrEnum):
    """SubstanceType defines the type of substance."""

    Active = "active"
    Inactive = "inactive"


class Substance(BaseModel):
    """Substance represents a single substance in a substance file."""

    name: str = Field(...)
    description: str = Field(...)
    type: SubstanceType = Field(default=SubstanceType.Active)
    concentration_unit: str
    waste_load_unit: Optional[str] = Field(default="-")


class Parameter(BaseModel):
    """Parameter represents a single parameter in a substance file."""

    name: str = Field(...)
    description: str = Field(...)
    unit: str = Field(...)
    value: float = Field(...)


class Output(BaseModel):
    """Output represents a single output in a substance file."""

    name: str = Field(...)
    description: str = Field(...)


class ActiveProcess(BaseModel):
    """ActiveProcess represents a single active process."""

    name: str = Field(...)
    description: str = Field(...)


class ActiveProcesses(BaseModel):
    """ActiveProcesses represents the collection of active processes in a substance file."""

    processes: List[ActiveProcess] = Field(default_factory=list)


class SubstanceModel(ParsableFileModel):
    """The overall substance model that contains the contents of one substance file (.sub).

    Attributes:
        substances: The substance definitions in the file.
        parameters: The parameter definitions in the file.
        outputs: The output variable definitions in the file.
        active_processes: The active processes block in the file.
    """

    serializer_config: SubstanceSerializerConfig = SubstanceSerializerConfig()

    substances: List[Substance] = Field(default_factory=list)
    parameters: List[Parameter] = Field(default_factory=list)
    outputs: List[Output] = Field(default_factory=list)
    active_processes: ActiveProcesses = Field(default_factory=ActiveProcesses)

    @classmethod
    def _ext(cls) -> str:
        return ".sub"

    @classmethod
    def _filename(cls) -> str:
        return "substance"

    @classmethod
    def _get_serializer(
        cls,
    ) -> Callable[[Path, Dict, SerializerConfig, ModelSaveSettings], None]:
        return SubstanceSerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable[[Path], Dict]:
        return SubstanceParser.parse

    @field_validator("parameters", mode="before")
    @classmethod
    def _replace_fortran_notation_in_parameters(
        cls, v: List[Any],
    ) -> List[Any]:
        """Convert Fortran scientific notation in parameter values."""
        for param in v:
            if isinstance(param, dict) and "value" in param:
                param["value"] = FortranUtils.replace_fortran_scientific_notation(
                    param["value"]
                )
        return v
