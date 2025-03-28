from pathlib import Path
from typing import Callable, Dict, List, Optional

from pydantic.v1 import Field

from hydrolib.core.basemodel import BaseModel, ModelSaveSettings, ParsableFileModel
from hydrolib.core.dflowfm.cmp.astronomicname import AstronomicName
from hydrolib.core.dflowfm.cmp.parser import CMPParser
from hydrolib.core.dflowfm.cmp.serializer import CMPSerializer


class HarmonicRecord(BaseModel):
    """Single cmp record, representing a harmonic component with amplitude and phase.

    Args:
        period (float): the period.
        amplitude (float): the amplitude.
        phase (float): the phase in degrees.

    Examples:
        Create a `HarmonicRecord` object from a dictionary:
            ```python
            >>> data = {
            ...     "period": 0.0,
            ...     "amplitude": 1.0,
            ...     "phase": 2.0
            ... }
            >>> harmonic_record = HarmonicRecord(**data)
            >>> print(harmonic_record.period)
            0.0

            ```
    Returns:
        HarmonicRecord: A new instance of the `HarmonicRecord` class.

    Raises:
        ValueError: If the period, amplitude or phase are not valid numbers.
    """

    period: float
    amplitude: float
    phase: float


class AstronomicRecord(BaseModel):
    """Single cmp record, representing an astronomic component with amplitude and phase.

    Args:
        name (AstronomicName): the astronomic name.
        amplitude (float): the amplitude.
        phase (float): the phase in degrees.

    Examples:
        Create an `AstronomicRecord` object from a dictionary:
            ```python
            >>> data = {
            ...     "name": "4MS10",
            ...     "amplitude": 1.0,
            ...     "phase": 2.0
            ... }
            >>> astronomic_record = AstronomicRecord(**data)
            >>> print(astronomic_record.name)
            4MS10

            ```
    Returns:
        AstronomicRecord: A new instance of the `AstronomicRecord` class.

    Raises:
        ValueError: If the name, amplitude or phase are not valid numbers.
    """

    name: AstronomicName
    amplitude: float
    phase: float


class CMPSet(BaseModel):
    """A CMP set containing harmonics and astronomics.

    Args:
        harmonics (List[HarmonicRecord]): A list containing the harmonic components.
        astronomics (List[AstronomicRecord]): A list containing the astronomic components.

    Examples:
        Create a `CmpSet` object from a dictionary:
            ```python
            >>> data = {
            ...     "astronomics": [{"name": "4MS10", "amplitude": 1.0, "phase": 2.0}]
            ... }
            >>> cmp_set = CMPSet(**data)
            >>> print(cmp_set.astronomics)
            [AstronomicRecord(name='4MS10', amplitude=1.0, phase=2.0)]

            ```
    Returns:
        CmpSet: A new instance of the `CmpSet` class.

    Raises:
        ValueError: If the harmonics or astronomics are not valid lists.
    """

    harmonics: Optional[List[HarmonicRecord]] = Field(default_factory=list)
    astronomics: Optional[List[AstronomicRecord]] = Field(default_factory=list)


class CMPModel(ParsableFileModel):
    """Class representing a cmp (*.cmp) file.
    This class is used to parse and serialize cmp files, which contain
    information about various components such as harmonics and astronomics.

    Args:
        comments (List[str]): A list with the header comment of the cmp file.
        components (List[CMPSet]): A list of CMPSet records where each entry represents one cmp file.

    Examples:
        Create a `CmpModel` object from a dictionary:
            ```python
            >>> data = {
            ...     "comments": ["# Example comment"],
            ...     "component": {
            ...         "harmonics": [{"period": 0.0, "amplitude": 1.0, "phase": 2.0}],
            ...         "astronomics": [{"name": "4MS10", "amplitude": 1.0, "phase": 2.0}]
            ...     }
            ... }
            >>> cmp_model = CMPModel(**data)
            >>> print(cmp_model.component.astronomics)
            [AstronomicRecord(name='4MS10', amplitude=1.0, phase=2.0)]

            ```

    Returns:
        CmpModel: A new instance of the `CmpModel` class.

    Raises:
        ValueError: If the comments or components are not valid lists.

    See Also:
        CmpSet: Class representing the components of the cmp file.
        CmpSerializer: Class responsible for serializing cmp files.
        CmpParser: Class responsible for parsing cmp files.
    """

    comments: List[str] = Field(default_factory=list)
    component: CMPSet = Field(default_factory=list)
    quantities_name: Optional[List[str]] = None

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
        return CMPSerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable[[Path], Dict]:
        return CMPParser.parse

    def get_units(self):
        """Return the units for each quantity in the timeseries.

        Returns:
            List[str]: A list of units for each quantity in the timeseries.

        Examples:
            Create a `CMPModel` object from a .cmp file:
                ```python
                >>> data = {
                ...     "comments": ["# Example comment"],
                ...     "component": {
                ...         "harmonics": [{"period": 0.0, "amplitude": 1.0, "phase": 2.0}],
                ...     },
                ...     "quantities_name": ["discharge"],
                ... }
                >>> model = CMPModel(**data)
                >>> print(model.get_units())
                ['m3/s']

                ```
        """
        if self.quantities_name is None:
            return None
        return get_quantity_unit(self.quantities_name)


def get_quantity_unit(quantities_names: List[str]) -> List[str]:
    """
    Maps each quantity in the input list to a specific unit based on its content.

    Args:
        quantities_names (List[str]): A list of strings to be checked for specific keywords.

    Returns:
        List[str]: A list of corresponding units for each input string.

    Examples:
        ```python
        >>> quantities_names = ["discharge", "waterlevel", "salinity", "temperature"]
        >>> get_quantity_unit(quantities_names)
        ['m3/s', 'm', '1e-3', 'degC']

        ```
    """
    # Define the mapping of keywords to units
    unit_mapping = {
        "discharge": "m3/s",
        "waterlevel": "m",
        "salinity": "1e-3",
        "temperature": "degC",
    }

    # Generate the list of units based on the mapping
    units = []
    for string in quantities_names:
        for keyword, unit in unit_mapping.items():
            if keyword in string.lower():
                units.append(unit)
                break
        else:
            # Append "-" if no keywords match
            units.append("-")

    return units
