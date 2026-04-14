"""Representation of a D-WAQ substance (.sub) file in various classes.

Most relevant classes are:

*   SubstanceModel: top-level class containing the whole .sub file contents.
*   Substance: a single substance (active or inactive) with concentration/waste-load units.
*   Parameter: a model parameter with name, unit, and numeric value.
*   Output: an output variable definition.
*   ActiveProcesses: collection of active water-quality processes.

See Also:
    SubstanceParser: Used for parsing .sub files.
    SubstanceSerializer: Used for serializing .sub files.
"""

from .models import (
    ActiveProcess,
    ActiveProcesses,
    Output,
    Parameter,
    Substance,
    SubstanceModel,
    SubstanceType,
)

__all__ = [
    "ActiveProcess",
    "ActiveProcesses",
    "Output",
    "Parameter",
    "Substance",
    "SubstanceModel",
    "SubstanceType",
]
