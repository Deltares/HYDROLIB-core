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
from typing import Any, Callable

from pydantic import Field, field_validator
from strenum import StrEnum

from hydrolib.core.base.models import (
    BaseModel,
    ParsableFileModel,
)
from hydrolib.core.base.utils import FortranUtils
from hydrolib.core.dflowfm.substance.parser import SubstanceParser
from hydrolib.core.dflowfm.substance.serializer import (
    SubstanceSerializer,
    SubstanceSerializerConfig,
)


class SubstanceType(StrEnum):
    """Enum class containing the valid substance types in a .sub file.

    A substance is either transported by the flow of water (``active``) or
    not transported by it, e.g. part of the sediment (``inactive``). Both
    active and inactive substances can be affected by water-quality processes.

    Attributes:
        Active (str):
            Substance that can be transported by the flow of water, i.e.
            dissolved and particulate material in the water column.
        Inactive (str):
            Substance that cannot be transported by the flow of water, e.g.
            substances that are part of the sediment.

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
    Inactive = "inactive"


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

    name: str = Field(
        ...,
        description="Substance identifier as it appears in the .sub file (a D-Water Quality state variable).",
    )
    description: str = Field(
        ...,
        description="Human-readable description of the substance.",
    )
    type: SubstanceType = Field(
        default=SubstanceType.Active,
        description=(
            "Whether the substance is active (transported by the flow of water) "
            "or inactive (not transported, e.g. part of the sediment)."
        ),
    )
    concentration_unit: str = Field(
        ...,
        description="Unit string for the substance concentration, e.g. '(g/m3)'.",
    )
    waste_load_unit: str | None = Field(
        default="-",
        description="Unit string for waste loads. Defaults to '-' (dimensionless).",
    )

    def is_active(self) -> bool:
        """Return whether this substance is actively computed.

        Returns:
            bool: True if the substance type is ``SubstanceType.Active``.
        """
        return self.type == SubstanceType.Active


class Parameter(BaseModel):
    """A single parameter definition in a D-WAQ substance file.

    Parameters define named numeric constants used by the water-quality
    processes. Values in the .sub file may use Fortran scientific notation
    (e.g. ``0.1500E+02``), which is automatically converted to a Python
    float during model construction.

    Attributes:
        name (str):
            Parameter identifier. Must be non-empty (a reserved
            character-string ID in D-Water Quality).
        description (str):
            Human-readable description.
        unit (str):
            Unit string, e.g. ``"(oC)"`` or ``"(-)"``.
        value (float):
            Numeric value of the parameter. Required: a well-formed .sub file
            always specifies a value (D-Water Quality uses ``-999`` as its
            missing-value sentinel, never ``0``), so a parameter block that
            omits the value line fails validation rather than defaulting.

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

    name: str = Field(
        ...,
        min_length=1,
        description="Process parameter identifier (a reserved character-string ID).",
    )
    description: str = Field(
        ...,
        description="Human-readable description of the process parameter.",
    )
    unit: str = Field(
        ...,
        description="Unit of the process parameter, e.g. '(oC)' or '(-)'.",
    )
    value: float = Field(
        ...,
        description=(
            "Numeric value of the process parameter. Required: D-Water Quality "
            "uses -999 as its missing-value sentinel (never 0), so a parameter "
            "block that omits the value line is rejected rather than defaulted."
        ),
    )


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

    name: str = Field(
        ...,
        description="Output variable identifier.",
    )
    description: str = Field(
        ...,
        description="Human-readable description of the output variable.",
    )


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

    name: str = Field(
        ...,
        description="Process identifier (e.g. 'RearOXY'), a reserved character-string ID from the process library.",
    )
    description: str = Field(
        ...,
        description="Human-readable description of the process (e.g. 'Reaeration of oxygen').",
    )


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

    processes: list[ActiveProcess] = Field(
        default_factory=list,
        description=(
            "List of active water-quality process entries. Empty when no "
            "processes are defined, in which case the block is omitted on serialization."
        ),
    )


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
        substances (list[Substance]):
            Substance definitions (active and/or inactive).
        parameters (list[Parameter]):
            Model parameter definitions with numeric values.
        outputs (list[Output]):
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

    serializer_config: SubstanceSerializerConfig = Field(
        default=SubstanceSerializerConfig(),
        description="Configuration controlling float formatting when writing the .sub file.",
    )
    substances: list[Substance] = Field(
        default_factory=list,
        description="Substance definitions (active and/or inactive).",
    )
    parameters: list[Parameter] = Field(
        default_factory=list,
        description="Process parameter definitions with numeric values.",
    )
    outputs: list[Output] = Field(
        default_factory=list,
        description="Output variable definitions.",
    )
    active_processes: ActiveProcesses = Field(
        default_factory=ActiveProcesses,
        description="Collection of active water-quality processes.",
    )

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
    def _get_parser(cls) -> Callable[[Path], dict]:
        return SubstanceParser.parse

    def get_active_substances(self) -> list[Substance]:
        """Return all substances with type ``SubstanceType.Active``.

        Returns:
            list[Substance]: Active substance definitions.
        """
        return [s for s in self.substances if s.is_active()]

    @field_validator("parameters", mode="before")
    @classmethod
    def _replace_fortran_notation_in_parameters(
        cls,
        v: list[Any],
    ) -> list[Any]:
        """Convert Fortran scientific notation in parameter values.

        Iterates over the raw parameter dicts and replaces Fortran-style
        notation (e.g. ``0.1500D+02``) with Python-compatible scientific
        notation (e.g. ``0.1500E+02``) so that Pydantic can coerce the
        string to a float.

        Args:
            v (list[Any]): Raw parameter list from the parser.

        Returns:
            list[Any]: Parameter list with Fortran notation replaced.
        """
        for param in v:
            if isinstance(param, dict) and "value" in param:
                param["value"] = FortranUtils.replace_fortran_scientific_notation(
                    param["value"]
                )
        return v
