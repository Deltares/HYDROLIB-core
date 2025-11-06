"""models.py defines all classes and functions related to representing substance files.
"""
from typing import Optional
from strenum import StrEnum
from pydantic.v1 import Field
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
    waste_load_unit: Optional[str] = Field(default='-')