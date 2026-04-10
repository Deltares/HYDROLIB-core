"""Representation of a D-WAQ substance (.sub) file in various model classes.

The .sub file format is used by Delft3D-WAQ (D-Water Quality) to define
substances, parameters, outputs, and active water-quality processes.

Most relevant classes are:

*   SubstanceModel: top-level class containing the full .sub file contents.
*   Substance: a single active or inactive substance definition.
*   Parameter: a model parameter with name, unit, and numeric value.
*   Output: an output variable definition.
*   ActiveProcesses: collection of active water-quality processes.
"""

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
    """Enum class containing the valid substance types in a .sub file.

    A substance is either actively computed by the water-quality engine
    (``active``) or carried along without reacting (``inactive``).

    Examples:
        - Access enum member values:
            ```python
            >>> from hydrolib.core.dflowfm.substance.models import SubstanceType
            >>> SubstanceType.Active.value
            'active'
            >>> SubstanceType.Inactive.value
            'inactive'

            ```
        - Compare with string values from a parsed file:
            ```python
            >>> from hydrolib.core.dflowfm.substance.models import SubstanceType
            >>> SubstanceType("inactive") == SubstanceType.Inactive
            True

            ```
    """

    Active = "active"
    """str: Substance is actively computed by the water-quality engine."""

    Inactive = "inactive"
    """str: Substance is carried along without reacting."""


class Substance(BaseModel):
    """A single substance definition in a D-WAQ substance file.

    Each substance block in a .sub file defines a named quantity with a type
    (active or inactive), a human-readable description, and units for
    concentration and waste load.

    Attributes:
        name (str):
            Substance identifier as it appears in the .sub file.
        description (str):
            Human-readable description of the substance.
        type (SubstanceType):
            Whether the substance is ``active`` or ``inactive``.
            Defaults to ``SubstanceType.Active``.
        concentration_unit (str):
            Unit string for concentrations, e.g. ``"(g/m3)"``.
        waste_load_unit (Optional[str]):
            Unit string for waste loads. Defaults to ``"-"`` (dimensionless).

    Examples:
        - Create an active substance and inspect its fields:
            ```python
            >>> from hydrolib.core.dflowfm.substance.models import Substance, SubstanceType
            >>> sub = Substance(
            ...     name="OXY",
            ...     description="Dissolved Oxygen",
            ...     concentration_unit="(g/m3)",
            ... )
            >>> sub.name
            'OXY'
            >>> sub.type == SubstanceType.Active
            True
            >>> sub.waste_load_unit
            '-'

            ```
        - Create an inactive substance:
            ```python
            >>> from hydrolib.core.dflowfm.substance.models import Substance, SubstanceType
            >>> sub = Substance(
            ...     name="DetCS1",
            ...     type="inactive",
            ...     description="DetC in layer S1",
            ...     concentration_unit="(gC/m2)",
            ... )
            >>> sub.type == SubstanceType.Inactive
            True
            >>> sub.concentration_unit
            '(gC/m2)'

            ```

    See Also:
        SubstanceType: Enum defining the allowed substance types.
        SubstanceModel: Top-level model that holds a list of substances.
    """

    name: str = Field(...)
    description: str = Field(...)
    type: SubstanceType = Field(default=SubstanceType.Active)
    concentration_unit: str
    waste_load_unit: Optional[str] = Field(default="-")


class Parameter(BaseModel):
    """A single parameter definition in a D-WAQ substance file.

    Parameters define named numeric constants used by the water-quality
    processes. Values in the .sub file may use Fortran scientific notation
    (e.g. ``0.1500E+02``), which is automatically converted to a Python
    float during model construction.

    Attributes:
        name (str):
            Parameter identifier.
        description (str):
            Human-readable description.
        unit (str):
            Unit string, e.g. ``"(oC)"`` or ``"(-)"``.
        value (float):
            Numeric value of the parameter.

    Examples:
        - Create a parameter and access its value:
            ```python
            >>> from hydrolib.core.dflowfm.substance.models import Parameter
            >>> param = Parameter(
            ...     name="Temp",
            ...     description="ambient water temperature",
            ...     unit="(oC)",
            ...     value=15.0,
            ... )
            >>> param.name
            'Temp'
            >>> param.value
            15.0

            ```
        - Fortran notation strings are converted to float automatically:
            ```python
            >>> from hydrolib.core.dflowfm.substance.models import Parameter
            >>> param = Parameter(
            ...     name="Special",
            ...     description="special value",
            ...     unit="(-)",
            ...     value="-999.0",
            ... )
            >>> param.value
            -999.0

            ```

    See Also:
        SubstanceModel: Top-level model that holds a list of parameters.
    """

    name: str = Field(...)
    """str: Parameter identifier."""

    description: str = Field(...)
    """str: Human-readable description."""

    unit: str = Field(...)
    """str: Unit string, e.g. ``'(oC)'``."""

    value: float = Field(...)
    """float: Numeric value of the parameter."""


class Output(BaseModel):
    """A single output variable definition in a D-WAQ substance file.

    Outputs define which computed quantities are written to the result files.

    Attributes:
        name (str):
            Output variable identifier.
        description (str):
            Human-readable description of the output.

    Examples:
        - Create an output and inspect it:
            ```python
            >>> from hydrolib.core.dflowfm.substance.models import Output
            >>> out = Output(name="Chlfa", description="Chlorophyll-a")
            >>> out.name
            'Chlfa'
            >>> out.description
            'Chlorophyll-a'

            ```

    See Also:
        SubstanceModel: Top-level model that holds a list of outputs.
    """

    name: str = Field(...)
    """str: Output variable identifier."""

    description: str = Field(...)
    """str: Human-readable description."""


class ActiveProcess(BaseModel):
    """A single active water-quality process entry.

    Each entry pairs a process identifier with a human-readable description.

    Attributes:
        name (str):
            Process identifier (e.g. ``"RearOXY"``).
        description (str):
            Human-readable description (e.g. ``"Reaeration of oxygen"``).

    Examples:
        - Create a process entry:
            ```python
            >>> from hydrolib.core.dflowfm.substance.models import ActiveProcess
            >>> proc = ActiveProcess(name="RearOXY", description="Reaeration of oxygen")
            >>> proc.name
            'RearOXY'

            ```

    See Also:
        ActiveProcesses: Container that holds a list of ActiveProcess entries.
    """

    name: str = Field(...)
    """str: Process identifier."""

    description: str = Field(...)
    """str: Human-readable description."""


class ActiveProcesses(BaseModel):
    """Container for the ``active-processes`` block in a D-WAQ substance file.

    Wraps a list of :class:`ActiveProcess` entries. When no processes are
    defined, the list is empty and the block is omitted during serialization.

    Attributes:
        processes (List[ActiveProcess]):
            List of active water-quality process entries.
            Defaults to an empty list.

    Examples:
        - Create an empty container:
            ```python
            >>> from hydrolib.core.dflowfm.substance.models import ActiveProcesses
            >>> procs = ActiveProcesses()
            >>> len(procs.processes)
            0

            ```
        - Create with process entries and iterate:
            ```python
            >>> from hydrolib.core.dflowfm.substance.models import ActiveProcess, ActiveProcesses
            >>> procs = ActiveProcesses(
            ...     processes=[
            ...         ActiveProcess(name="RearOXY", description="Reaeration of oxygen"),
            ...         ActiveProcess(name="BLOOM_P", description="BLOOM II algae module"),
            ...     ]
            ... )
            >>> len(procs.processes)
            2
            >>> procs.processes[0].name
            'RearOXY'

            ```

    See Also:
        ActiveProcess: Individual process entry.
        SubstanceModel: Top-level model containing this block.
    """

    processes: List[ActiveProcess] = Field(default_factory=list)


class SubstanceModel(ParsableFileModel):
    """Top-level model representing the contents of a D-WAQ substance file (.sub).

    This model reads, validates, and writes .sub files used by D-Water Quality.
    The file format is block-based with four block types: ``substance``,
    ``parameter``, ``output``, and ``active-processes``. Fortran scientific
    notation in parameter values (e.g. ``0.1500E+02``) is automatically
    converted to Python floats during loading.

    Attributes:
        serializer_config (SubstanceSerializerConfig):
            Configuration for serialization of the .sub file.
        substances (List[Substance]):
            Substance definitions (active and/or inactive).
        parameters (List[Parameter]):
            Model parameter definitions with numeric values.
        outputs (List[Output]):
            Output variable definitions.
        active_processes (ActiveProcesses):
            Collection of active water-quality processes.

    Examples:
        - Create an empty model and add a substance:
            ```python
            >>> from hydrolib.core.dflowfm.substance.models import SubstanceModel, Substance
            >>> model = SubstanceModel()
            >>> len(model.substances)
            0
            >>> model.substances.append(
            ...     Substance(name="OXY", description="Dissolved Oxygen", concentration_unit="(g/m3)")
            ... )
            >>> len(model.substances)
            1

            ```
        - Load from a .sub file and inspect contents:
            ```python
            >>> from hydrolib.core.dflowfm.substance.models import SubstanceModel
            >>> model = SubstanceModel(filepath="tests/data/input/substances/substance-file.sub")
            >>> len(model.substances)
            2
            >>> model.substances[0].name
            'Any-substance-name-1'
            >>> model.parameters[0].name
            'Any-Parameter-name-1'

            ```

    See Also:
        SubstanceParser: Parser used to read .sub files.
        SubstanceSerializer: Serializer used to write .sub files.
        SubstanceSerializerConfig: Configuration for float formatting during serialization.

    References:
        - `D-Flow FM User Manual <https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf>`_
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
    ) -> Callable[..., None]:
        return SubstanceSerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable[[Path], Dict]:
        return SubstanceParser.parse

    @field_validator("parameters", mode="before")
    @classmethod
    def _replace_fortran_notation_in_parameters(
        cls,
        v: List[Any],
    ) -> List[Any]:
        """Convert Fortran scientific notation in parameter values.

        Iterates over the raw parameter dicts and replaces Fortran-style
        notation (e.g. ``0.1500D+02``) with Python-compatible scientific
        notation (e.g. ``0.1500E+02``) so that Pydantic can coerce the
        string to a float.

        Args:
            v (List[Any]): Raw parameter list from the parser.

        Returns:
            List[Any]: Parameter list with Fortran notation replaced.
        """
        for param in v:
            if isinstance(param, dict) and "value" in param:
                param["value"] = FortranUtils.replace_fortran_scientific_notation(
                    param["value"]
                )
        return v
