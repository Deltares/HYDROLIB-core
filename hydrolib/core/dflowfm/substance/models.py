"""models.py defines all classes and functions related to representing substance files.
"""

from strenum import StrEnum

class SubstanceType(StrEnum):
    """SubstanceType defines the type of substance."""
    Active = "Active"
    Inactive = "Inactive"


