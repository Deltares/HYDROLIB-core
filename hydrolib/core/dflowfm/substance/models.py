"""models.py defines all classes and functions related to representing substance files.
"""

from typing import List, Optional

from pydantic.v1 import Field
from strenum import StrEnum

from hydrolib.core.base.models import BaseModel


class SubstanceType(StrEnum):
    """SubstanceType defines the type of substance."""

    Active = "Active"
    Inactive = "Inactive"


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
