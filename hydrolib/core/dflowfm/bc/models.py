"""Representation of a .bc file in various classes.

Most relevant classes are:

*   ForcingModel: toplevel class containing the whole .bc file contents.
*   ForcingBase subclasses: containing the actual data columns, for example:
    TimeSeries, HarmonicComponent, AstronomicComponent, HarmonicCorrection,
    AstronomicCorrection, Constant, T3D.

"""

import logging
import re
from pathlib import Path
from typing import Any, Callable, Dict, Iterator, List, Literal, Optional, Set, Union

from pydantic.v1 import Extra
from pydantic.v1.class_validators import root_validator, validator
from pydantic.v1.fields import Field
from strenum import StrEnum

from hydrolib.core.base.models import BaseModel, ModelSaveSettings
from hydrolib.core.base.utils import to_list
from hydrolib.core.dflowfm.ini.io_models import Property, Section
from hydrolib.core.dflowfm.ini.models import (
    DataBlockINIBasedModel,
    INIGeneral,
    INIModel,
)
from hydrolib.core.dflowfm.ini.parser import Parser, ParserConfig
from hydrolib.core.dflowfm.ini.serializer import DataBlockINIBasedSerializerConfig
from hydrolib.core.dflowfm.ini.util import (
    get_enum_validator,
    get_from_subclass_defaults,
    get_split_string_on_delimiter_validator,
    get_type_based_on_subclass_default_value,
    make_list_validator,
    rename_keys_for_backwards_compatibility,
)

logger = logging.getLogger(__name__)


class VerticalInterpolation(StrEnum):
    """Enum class containing the valid values for the vertical position type,
    which defines what the numeric values for vertical position specification mean.
    """

    linear = "linear"
    """str: Linear interpolation between vertical positions."""

    log = "log"
    """str: Logarithmic interpolation between vertical positions (e.g. vertical velocity profiles)."""

    block = "block"
    """str: Equal to the value at the directly lower specified vertical position."""


class VerticalPositionType(StrEnum):
    """Enum class containing the valid values for the vertical position type."""

    percentage_bed = "percBed"
    """str: Percentage with respect to the water depth from the bed upward."""

    z_bed = "ZBed"
    """str: Absolute distance from the bed upward."""

    z_datum = "ZDatum"
    """str: z-coordinate with respect to the reference level of the model."""

    z_surf = "ZSurf"
    """str: Absolute distance from the free surface downward."""


class TimeInterpolation(StrEnum):
    """Enum class containing the valid values for the time interpolation."""

    linear = "linear"
    """str: Linear interpolation between times."""

    block_from = "block-From"
    """str: Equal to that at the start of the time interval (latest specified time value)."""

    block_to = "block-To"
    """str: Equal to that at the end of the time interval (upcoming specified time value)."""


class QuantityUnitPair(BaseModel):
    """A .bc file header lines tuple containing a quantity name, its unit and optionally a vertical position index."""

    quantity: str
    """str: Name of quantity."""

    unit: str
    """str: Unit of quantity."""

    vertpositionindex: Optional[int] = Field(alias="vertPositionIndex")
    """int (optional): This is a (one-based) index into the verticalposition-specification, assigning a vertical position to the quantity (t3D-blocks only)."""

    def _to_properties(self):
        """Generator function that yields the ini Property objects for a single
        QuantityUnitPair object."""
        yield Property(key="quantity", value=self.quantity)
        yield Property(key="unit", value=self.unit)
        if self.vertpositionindex is not None:
            yield Property(key="vertPositionIndex", value=self.vertpositionindex)


class VectorQuantityUnitPairs(BaseModel):
    """A subset of .bc file header lines containing a vector quantity definition,
    followed by all component quantity names, their unit and optionally their
    vertical position indexes."""

    class Config:
        validate_assignment = True

    vectorname: str
    """str: Name of the vector quantity."""

    elementname: List[str]
    """List[str]: List of names of the vector component quantities."""

    quantityunitpair: List[QuantityUnitPair]
    """List[QuantityUnitPair]: List of QuantityUnitPair that define the vector components."""

    @root_validator
    @classmethod
    def _validate_quantity_element_names(cls, values: Dict):
        for idx, name in enumerate(
            [qup.quantity for qup in values["quantityunitpair"]]
        ):
            if name not in values["elementname"]:
                raise ValueError(
                    f"quantityunitpair[{idx}], quantity '{name}' must be in vectordefinition's element names: '{VectorQuantityUnitPairs._to_vectordefinition_string(values['vectorname'], values['elementname'])}'."
                )

        return values

    @staticmethod
    def _to_vectordefinition_string(vectorname: str, elementname: List[str]):
        return vectorname + ":" + ",".join(elementname)

    def __str__(self) -> str:
        return VectorQuantityUnitPairs._to_vectordefinition_string(
            self.vectorname, self.elementname
        )

    def _to_properties(self):
        """Generator function that yields the ini Property objects for a single
        VectorQuantityUnitPairs object."""
        yield Property(key="vector", value=str(self))

        for qup in self.quantityunitpair:
            for prop in qup._to_properties():
                yield prop


ScalarOrVectorQUP = Union[QuantityUnitPair, VectorQuantityUnitPairs]


class ForcingBase(DataBlockINIBasedModel):
    """
    The base class of a single [Forcing] block in a .bc forcings file.

    The `ForcingBase` class is used as the foundational model for various types
    of forcing data blocks, such as TimeSeries, Harmonic, Astronomic, and others.
    It includes functionality for handling structured data, validating input,
    and serializing the forcing data.

    This model is referenced under a [ForcingModel][hydrolib.core.dflowfm.bc.models.ForcingModel]`.forcing[..]`.

    Attributes:
        name (str):
            Unique identifier that specifies the location for this forcing data.
        function (str):
            Specifies the function type of the data in the associated data block.
        quantityunitpair (List[ScalarOrVectorQUP]):
            List of header lines for one or more quantities and their units.
            These describe the columns in the associated data block.

    Args:
        name (str):
            The unique name identifying this forcing block.
        function (str):
            The function type specifying the behavior of the forcing block.
            Possible values are timeseries, harmonic, astronomic, harmonic-correction, astronomic-correction, t3d,
            constant, qhtable.
        quantityunitpair (List[ScalarOrVectorQUP]):
            The quantities and units associated with the data block.

    Returns:
        None

    Raises:
        ValueError: If `quantity` or `unit` fields are missing or mismatched.
        ValueError: If the `function` field contains an unrecognized type.

    See Also:
        DataBlockINIBasedModel: Parent class for handling data blocks in INI files.
        QuantityUnitPair: Represents a single quantity and its unit.
        VectorQuantityUnitPairs: Handles vector quantities in the data block.

    Examples:
        Create a simple forcing block:

            ```python
            >>> from hydrolib.core.dflowfm.bc.models import ForcingBase, QuantityUnitPair
            >>> forcing = ForcingBase(
            ...     name="Location1",
            ...     function="timeseries",
            ...     quantityunitpair=[QuantityUnitPair(quantity="waterlevel", unit="m")]
            ... )
            >>> print(forcing.name)
            Location1
            >>> print(forcing.function)
            timeseries

            ```

        Handle vector quantities:

            ```python
            >>> from hydrolib.core.dflowfm.bc.models import VectorQuantityUnitPairs
            >>> forcing = ForcingBase(
            ...     name="Location2",
            ...     function="vector",
            ...     quantityunitpair=[
            ...         VectorQuantityUnitPairs(
            ...             vectorname="velocity",
            ...             elementname=["u", "v"],
            ...             quantityunitpair=[
            ...                 QuantityUnitPair(quantity="u", unit="m/s"),
            ...                 QuantityUnitPair(quantity="v", unit="m/s")
            ...             ]
            ...         )
            ...     ]
            ... )
            >>> print(forcing.quantityunitpair[0].vectorname)
            velocity

            ```

    Notes:
        - The `ForcingBase` class is typically subclassed to provide specific behavior for different forcing types.
        - It includes robust validation mechanisms to ensure consistency between quantities and units.
    """

    _header: Literal["Forcing"] = "Forcing"
    name: str = Field(alias="name")
    """str: Unique identifier that identifies the location for this forcing data."""

    function: str = Field(alias="function")
    """str: Function type of the data in the actual datablock."""

    quantityunitpair: List[ScalarOrVectorQUP]
    """List[ScalarOrVectorQUP]: List of header lines for one or more quantities and their unit. Describes the columns in the actual datablock."""

    def _exclude_fields(self) -> Set:
        return {"quantityunitpair"}.union(super()._exclude_fields())

    @classmethod
    def _supports_comments(cls):
        return True

    @classmethod
    def _duplicate_keys_as_list(cls):
        return True

    @root_validator(pre=True)
    def _validate_quantityunitpair(cls, values):
        quantityunitpairkey = "quantityunitpair"

        if values.get(quantityunitpairkey) is not None:
            return values

        quantities = values.get("quantity")
        if quantities is None:
            raise ValueError("quantity is not provided")
        units = values.get("unit")
        if units is None:
            raise ValueError("unit is not provided")

        if isinstance(quantities, str) and isinstance(units, str):
            values[quantityunitpairkey] = [
                QuantityUnitPair(quantity=quantities, unit=units)
            ]
            return values

        if isinstance(quantities, list) and isinstance(units, list):
            if len(quantities) != len(units):
                raise ValueError(
                    "Number of quantities should be equal to number of units"
                )

            values[quantityunitpairkey] = [
                QuantityUnitPair(quantity=quantity, unit=unit)
                for quantity, unit in zip(quantities, units)
            ]
            return values

        raise ValueError("Number of quantities should be equal to number of units")

    @validator("function", pre=True)
    def _set_function(cls, value):
        return get_from_subclass_defaults(ForcingBase, "function", value)

    @classmethod
    def validate(cls, v):
        """Try to initialize subclass based on the `function` field.
        This field is compared to each `function` field of the derived models of `ForcingBase`
        or models derived from derived models.
        The derived model with an equal function type will be initialized.

        Raises:
            ValueError: When the given type is not a known structure type.
        """

        # should be replaced by discriminated unions once merged
        # https://github.com/samuelcolvin/pydantic/pull/2336
        if isinstance(v, dict):
            function_string = v.get("function", "").lower()
            function_type = get_type_based_on_subclass_default_value(
                cls, "function", function_string
            )

            if function_type is not None:
                return function_type(**v)

            else:
                raise ValueError(
                    f"Function of {cls.__name__} with name={v.get('name', '')} and function={v.get('function', '')} is not recognized."
                )
        return v

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("name")

    def _to_section(
        self,
        config: DataBlockINIBasedSerializerConfig,
        save_settings: ModelSaveSettings,
    ) -> Section:
        section = super()._to_section(config, save_settings)

        for quantity in self.quantityunitpair:
            for prop in quantity._to_properties():
                section.content.append(prop)

        return section

    class Config:
        extra = Extra.ignore

    def __repr__(self) -> str:
        data = dict(self)
        data["datablock"] = "<omitted>"
        representable = BaseModel.construct(**data)
        return str(representable)


class VectorForcingBase(ForcingBase):
    """
    The base class of a single [Forcing] block that supports vectors in a .bc forcings file.
    """

    @root_validator(pre=True)
    def validate_and_update_quantityunitpairs(cls, values: Dict) -> Dict:
        """
        Validates and, if required, updates vector quantity unit pairs.

        Args:
            values (Dict): Dictionary of values to be used to validate or
            update vector quantity unit pairs.

        Raises:
            ValueError: When a quantity unit pair is found in a vector where it does not belong.
            ValueError: When the number of quantity unit pairs in a vectors is not as expected.

        Returns:
            Dict: Dictionary of validates values.
        """
        quantityunitpairs = values["quantityunitpair"]
        vector = values.get("vector")
        number_of_element_repetitions = cls.get_number_of_repetitions(values)

        VectorForcingBase._process_vectordefinition_or_check_quantityunitpairs(
            vector, quantityunitpairs, number_of_element_repetitions
        )

        return values

    @staticmethod
    def _process_vectordefinition_or_check_quantityunitpairs(
        vectordefs: Optional[List[str]],
        quantityunitpairs: List[ScalarOrVectorQUP],
        number_of_element_repetitions: int,
    ) -> None:
        """
        Processes the given vector definition header lines from a .bc file
        or, if absent, checks whether the existing VectorQuantityUnitPairs
        objects already have the correct vector length.

        Args:
            vectordefs (List[str]): List of vector definition values, e.g.,
                ["vectorname:comp1,comp2,..compN", ...]
            quantityunitpairs (List[ScalarOrVectorQUP]): list of already parsed
                and constructed QuantityUnitPair objects, which may be modified
                in place with some packed VectorQuantityUnitPairs objects.
            number_of_element_repetitions (int, optional): Number of times each
                vector element is expected to be present in the subsequent
                Quantity lines. Typically used for 3D quantities, using the
                number of vertical layers.
        """

        if vectordefs is not None and not any(
            map(lambda qup: isinstance(qup, VectorQuantityUnitPairs), quantityunitpairs)
        ):
            # Vector definition line still must be processed and VectorQUPs still created.
            VectorForcingBase._validate_vectordefinition_and_update_quantityunitpairs(
                vectordefs, quantityunitpairs, number_of_element_repetitions
            )
        else:
            # VectorQUPs already present; directly validate their vector length.
            for qup in quantityunitpairs:
                if isinstance(qup, VectorQuantityUnitPairs):
                    VectorForcingBase._validate_vectorlength(
                        qup, number_of_element_repetitions
                    )

    @staticmethod
    def _validate_vectordefinition_and_update_quantityunitpairs(
        vectordefs: Optional[List[str]],
        quantityunitpairs: List[ScalarOrVectorQUP],
        number_of_element_repetitions: int,
    ) -> None:
        """
        Validates the given vector definition header lines from a .bc file
        for a ForcingBase subclass and updates the existing QuantityUnitPair list
        by packing the vector elements into a VectorQuantityUnitPairs object
        for each vector definition.

        Args:
            vectordefs (List[str]): List of vector definition values, e.g.,
                ["vectorname:comp1,comp2,..compN", ...]
            quantityunitpairs (List[ScalarOrVectorQUP]): list of already parsed
                and constructed QuantityUnitPair objects, which will be modified
                in place with some packed VectorQuantityUnitPairs objects.
            number_of_element_repetitions (int, optional): Number of times each
                vector element is expected to be present in the subsequent
                Quantity lines. Typically used for 3D quantities, using the
                number of vertical layers.
        """

        if vectordefs is None:
            return

        vectordefs = to_list(vectordefs)

        qup_iter = iter(quantityunitpairs)

        # Start a new list, to only keep the scalar QUPs, and add newly
        # created VectorQUPs.
        quantityunitpairs_with_vectors = []

        # If one quantity is "time", it must be the first one.
        if quantityunitpairs[0].quantity == "time":
            quantityunitpairs_with_vectors.append(quantityunitpairs[0])
            _ = next(qup_iter)

        # For each vector definition line, greedily find the quantity unit pairs
        # that form the vector elements, and pack them into a single VectorQuantityUnitPairs oject.
        for vectordef in vectordefs:
            VectorForcingBase._find_and_pack_vector_qups(
                number_of_element_repetitions,
                qup_iter,
                quantityunitpairs_with_vectors,
                vectordef,
            )

        for remaining_qu_pair in qup_iter:
            quantityunitpairs_with_vectors.append(remaining_qu_pair)

        quantityunitpairs[:] = quantityunitpairs_with_vectors

    @staticmethod
    def _find_and_pack_vector_qups(
        number_of_element_repetitions: int,
        qup_iter: Iterator[ScalarOrVectorQUP],
        quantityunitpairs_with_vectors: List[ScalarOrVectorQUP],
        vectordef: str,
    ):
        vectorname, componentdefs = vectordef.split(":")
        componentnames = re.split(r"[, \t]", componentdefs)
        n_components = len(componentnames)

        vqu_pair = VectorQuantityUnitPairs(
            vectorname=vectorname, elementname=componentnames, quantityunitpair=[]
        )

        n_rep = 0
        for qu_pair in qup_iter:
            if qu_pair.quantity in componentnames:
                # This vector element found, store it.
                vqu_pair.quantityunitpair.append(qu_pair)
                n_rep += 1
                if n_rep == n_components * number_of_element_repetitions:
                    break
            else:
                # This quantity was no vector element being searched for
                # so keep it as a regular (scalar) QuantityUnitPair.
                quantityunitpairs_with_vectors.append(qu_pair)

        if VectorForcingBase._validate_vectorlength(
            vqu_pair, number_of_element_repetitions
        ):
            # This VectorQuantityUnitPairs is now complete; add it to result list.
            quantityunitpairs_with_vectors.append(vqu_pair)

    @staticmethod
    def _validate_vectorlength(
        vqu_pair: VectorQuantityUnitPairs,
        number_of_element_repetitions,
    ) -> bool:
        """
        Checks whether the number of QuantityUnitPairs in a vector quantity
        matches exactly with number of vector elements in the definition and,
        optionally, the number of vertical layers.

        Args:
            vqu_pair (VectorQuantityUnitPairs): the vector quantity object to be checked.
            number_of_element_repetitions (int, optional): Number of times each
                vector element is expected to be present in the subsequent
                Quantity lines. Typically used for 3D quantities, using the
                number of vertical layers.

        Returns:
            bool: True if vqu_pair is valid. False return value is hidden because
                an exception will be raised.

        Raises:
            ValueError: If number of QuantityUnitPair objects in vqu_pair is not equal
                to number of element names * number_of_element_repetitions.
        """

        if not (
            valid := len(vqu_pair.quantityunitpair)
            == len(vqu_pair.elementname) * number_of_element_repetitions
        ):
            raise ValueError(
                f"Incorrect number of quantity unit pairs were found; should match the elements in vectordefinition for {vqu_pair.vectorname}"
                + (
                    f", and {number_of_element_repetitions} vertical layers"
                    if number_of_element_repetitions > 1
                    else ""
                )
                + "."
            )

        return valid

    @validator("function", pre=True)
    def _set_function(cls, value):
        return get_from_subclass_defaults(VectorForcingBase, "function", value)

    @classmethod
    def get_number_of_repetitions(cls, values: Dict) -> int:
        """Gets the number of expected quantityunitpairs for each vector element. Defaults to 1."""
        return 1


class TimeSeries(VectorForcingBase):
    """Subclass for a .bc file [Forcing] block with timeseries data.

    Attributes:
        function (Literal["timeseries"]):
            Specifies that this is a timeseries forcing block. Defaults to "timeseries".
        timeinterpolation (TimeInterpolation):
            The type of time interpolation, such as "linear", "block-From", or "block-To".
        offset (float):
            All values in the table are increased by the offset (after multiplication by factor).
            Defaults to 0.0.
        factor (float):
            All values in the table are multiplied by the factor. Defaults to 1.0.

     Methods:
        rename_keys(cls, values: Dict) -> Dict:
            Renames old keywords to currently supported keywords for backward compatibility.

    Examples:
        One quantity:
        ```python
        >>> from hydrolib.core.dflowfm.bc.models import TimeSeries
        >>> timeseries = TimeSeries(
        ...     name="Boundary1",
        ...     function="timeseries",
        ...     timeinterpolation="block-From",
        ...     offset=1.23,
        ...     factor=2.34,
        ...     quantityunitpair=[
        ...         QuantityUnitPair(quantity="time", unit="minutes since 2015-01-01 00:00:00"),
        ...         QuantityUnitPair(quantity="waterlevel", unit="m")
        ...    ],
        ...     datablock=[["0", "10"], ["1.0", "20"], ["2.0", "30"]]
        ... )

        ```
        the forcing will look as follows:
        ```
        [Forcing]
            name              = Boundary1
            timeinterpolation = block-From
            function          = timeseries
            quantity          = time
            unit              = minutes since 2001-01-01
            quantity          = waterlevel
            unit              = m
            offset            = 1.23
            factor            = 2.34
            0 10
            1 20
            2 30
        ```
        Two quantities:
        >>> timeseries = TimeSeries(
        ...     name="Boundary1",
        ...     function="timeseries",
        ...     timeinterpolation="block-From",
        ...     offset=1.23,
        ...     factor=2.34,
        ...     quantityunitpair=[
        ...         QuantityUnitPair(quantity="time", unit="minutes since 2015-01-01 00:00:00"),
        ...         QuantityUnitPair(quantity="dischargebnd", unit="m³/s"),
        ...         QuantityUnitPair(quantity="waterlevelbnd", unit="m")
        ...     ],
        ...    datablock=[["0", "50", "4.0"], ["1", "60", "5.0"], ["2", "70", "6.0"]]
        ... )

        ```
        the forcing will look as follows:
        ```
        [Forcing]
            name              = Boundary1
            timeinterpolation = block-From
            function          = timeseries
            quantity          = time
            unit              = minutes since 2015-01-01 00:00:00
            quantity          = dischargebnd
            unit              = m³/s
            quantity          = waterlevelbnd
            unit              = m
            offset            = 1.23
            factor            = 2.34
            0 50 4.0
            1 60 5.0
            2 70 6.0
        ```
    """

    function: Literal["timeseries"] = "timeseries"

    timeinterpolation: TimeInterpolation = Field(alias="timeInterpolation")
    """TimeInterpolation: The type of time interpolation."""

    offset: float = Field(0.0, alias="offset")
    """float: All values in the table are increased by the offset (after multiplication by factor). Defaults to 0.0."""

    factor: float = Field(1.0, alias="factor")
    """float: All values in the table are multiplied with the factor. Defaults to 1.0."""

    _timeinterpolation_validator = get_enum_validator(
        "timeinterpolation", enum=TimeInterpolation
    )

    @root_validator(allow_reuse=True, pre=True)
    def rename_keys(cls, values: Dict) -> Dict:
        """Renames some old keywords to the currently supported keywords."""
        return rename_keys_for_backwards_compatibility(
            values,
            {
                "timeinterpolation": ["time_interpolation"],
            },
        )


class Harmonic(ForcingBase):
    """Subclass for a .bc file [Forcing] block with harmonic components data."""

    function: Literal["harmonic"] = "harmonic"

    factor: float = Field(1.0, alias="factor")
    """float: All values in the table are multiplied with the factor. Defaults to 1.0."""


class Astronomic(ForcingBase):
    """Subclass for a .bc file [Forcing] block with astronomic components data."""

    function: Literal["astronomic"] = "astronomic"

    factor: float = Field(1.0, alias="factor")
    """float: All values in the table are multiplied with the factor. Defaults to 1.0."""


class HarmonicCorrection(ForcingBase):
    """Subclass for a .bc file [Forcing] block with harmonic components correction data."""

    function: Literal["harmonic-correction"] = "harmonic-correction"


class AstronomicCorrection(ForcingBase):
    """Subclass for a .bc file [Forcing] block with astronomic components correction data."""

    function: Literal["astronomic-correction"] = "astronomic-correction"


class T3D(VectorForcingBase):
    """Subclass for a .bc file [Forcing] block with 3D timeseries data.

    Args:
        offset (float): default is 0.0
            All values in the table are increased by the offset (after multiplication by factor).
        factor (float): default is 1.0
            all values in the table are multiplied with the factor.
        vertpositions (List[float]):
            The specification of the vertical positions.
        vertinterpolation (VerticalInterpolation): default is linear
            The type of vertical interpolation.
        vertpositiontype (VerticalPositionType):
            The vertical position type of the verticalpositions values.
        timeinterpolation (TimeInterpolation): default is linear
            The type of time interpolation.

    Examples:

    """

    function: Literal["t3d"] = "t3d"
    offset: float = Field(0.0, alias="offset")
    factor: float = Field(1.0, alias="factor")
    vertpositions: List[float] = Field(alias="vertPositions")
    vertinterpolation: VerticalInterpolation = Field(
        VerticalInterpolation.linear, alias="vertInterpolation"
    )
    vertpositiontype: VerticalPositionType = Field(alias="vertPositionType")
    timeinterpolation: TimeInterpolation = Field(
        TimeInterpolation.linear, alias="timeInterpolation"
    )

    _keys_to_rename = {
        "timeinterpolation": ["time_interpolation"],
        "vertpositions": ["vertical_position_specification"],
        "vertinterpolation": ["vertical_interpolation"],
        "vertpositiontype": ["vertical_position_type"],
        "vertpositionindex": ["vertical_position"],
    }

    @root_validator(allow_reuse=True, pre=True)
    def rename_keys(cls, values: Dict) -> Dict:
        """Renames some old keywords to the currently supported keywords."""
        return rename_keys_for_backwards_compatibility(values, cls._keys_to_rename)

    _split_to_list = get_split_string_on_delimiter_validator(
        "vertpositions",
    )

    _verticalinterpolation_validator = get_enum_validator(
        "vertinterpolation", enum=VerticalInterpolation
    )
    _verticalpositiontype_validator = get_enum_validator(
        "vertpositiontype",
        enum=VerticalPositionType,
        alternative_enum_values={
            VerticalPositionType.percentage_bed: ["percentage from bed"],
        },
    )
    _timeinterpolation_validator = get_enum_validator(
        "timeinterpolation", enum=TimeInterpolation
    )

    @classmethod
    def get_number_of_repetitions(cls, values: Dict) -> int:
        verticalpositions = values.get("vertpositions")
        # Since the renaming root validator may not have been run yet, in this
        # method we explicitly check old keywords for backwards compatibility:
        if verticalpositions is None:
            # try to get the value from any of the older keywords
            for old_keyword in cls._keys_to_rename["vertpositions"]:
                verticalpositions = values.get(old_keyword)
                if verticalpositions is not None:
                    break

        if verticalpositions is None:
            raise ValueError("vertPositions is not provided")

        number_of_verticalpositions = (
            len(verticalpositions)
            if isinstance(verticalpositions, List)
            else len(verticalpositions.split())
        )

        return number_of_verticalpositions

    @root_validator(pre=True)
    def _validate_quantityunitpairs(cls, values: Dict) -> Dict:
        quantityunitpairs = values["quantityunitpair"]

        T3D._validate_that_first_unit_is_time_and_has_no_verticalposition(
            quantityunitpairs
        )

        number_of_verticalpositions = cls.get_number_of_repetitions(values)

        verticalpositionindexes = values.get("vertpositionindex")
        if verticalpositionindexes is None:
            T3D._validate_that_all_quantityunitpairs_have_valid_verticalpositionindex(
                quantityunitpairs[1:], number_of_verticalpositions
            )
        else:
            T3D._validate_verticalpositionindexes_and_update_quantityunitpairs(
                verticalpositionindexes,
                number_of_verticalpositions,
                quantityunitpairs,
            )

        return values

    @staticmethod
    def _validate_that_first_unit_is_time_and_has_no_verticalposition(
        quantityunitpairs: List[QuantityUnitPair],
    ) -> None:
        if quantityunitpairs[0].quantity.lower() != "time":
            raise ValueError("First quantity should be `time`")
        if quantityunitpairs[0].vertpositionindex is not None:
            raise ValueError("`time` quantity cannot have vertical position index")

    @staticmethod
    def _validate_that_all_quantityunitpairs_have_valid_verticalpositionindex(
        quantityunitpairs: List[ScalarOrVectorQUP], maximum_verticalpositionindex: int
    ) -> None:
        for quantityunitpair in quantityunitpairs:
            if isinstance(quantityunitpair, VectorQuantityUnitPairs):
                return T3D._validate_that_all_quantityunitpairs_have_valid_verticalpositionindex(
                    quantityunitpair.quantityunitpair, maximum_verticalpositionindex
                )

            verticalpositionindex = quantityunitpair.vertpositionindex

            if not T3D._is_valid_verticalpositionindex(
                verticalpositionindex, maximum_verticalpositionindex
            ):
                raise ValueError(
                    f"Vertical position index should be between 1 and {maximum_verticalpositionindex}, but {verticalpositionindex} was given"
                )

    @staticmethod
    def _validate_verticalpositionindexes_and_update_quantityunitpairs(
        verticalpositionindexes: List[int],
        number_of_verticalpositions: int,
        quantityunitpairs: List[ScalarOrVectorQUP],
    ) -> None:
        if verticalpositionindexes is None:
            raise ValueError("vertPositionIndex is not provided")

        T3D._validate_that_verticalpositionindexes_are_valid(
            verticalpositionindexes, number_of_verticalpositions
        )

        T3D._add_verticalpositionindex_to_quantityunitpairs(
            quantityunitpairs[1:], verticalpositionindexes
        )

    @staticmethod
    def _validate_that_verticalpositionindexes_are_valid(
        verticalpositionindexes: List[int], number_of_vertical_positions: int
    ) -> None:
        for verticalpositionindexstring in verticalpositionindexes:
            verticalpositionindex = (
                int(verticalpositionindexstring)
                if verticalpositionindexstring
                else None
            )
            if not T3D._is_valid_verticalpositionindex(
                verticalpositionindex, number_of_vertical_positions
            ):
                raise ValueError(
                    f"Vertical position index should be between 1 and {number_of_vertical_positions}"
                )

    @staticmethod
    def _is_valid_verticalpositionindex(
        verticalpositionindex: int, number_of_vertical_positions: int
    ) -> bool:
        one_based_index_offset = 1

        return (
            verticalpositionindex is not None
            and verticalpositionindex >= one_based_index_offset
            and verticalpositionindex <= number_of_vertical_positions
        )

    @staticmethod
    def _add_verticalpositionindex_to_quantityunitpairs(
        quantityunitpairs: List[ScalarOrVectorQUP], verticalpositionindexes: List[int]
    ) -> None:
        i = 0

        for quanityunitpair in quantityunitpairs:
            if i >= len(verticalpositionindexes):
                raise ValueError(
                    "Number of vertical position indexes should be equal to the number of quantities/units - 1"
                )

            if isinstance(quanityunitpair, VectorQuantityUnitPairs):
                for qup in quanityunitpair.quantityunitpair:
                    qup.vertpositionindex = verticalpositionindexes[i]
                    i = i + 1
            else:
                quanityunitpair.vertpositionindex = verticalpositionindexes[i]
                i = i + 1

        if i != len(verticalpositionindexes):
            raise ValueError(
                "Number of vertical position indexes should be equal to the number of quantities/units - 1"
            )


class QHTable(ForcingBase):
    """Subclass for a .bc file [Forcing] block with Q-h table data."""

    function: Literal["qhtable"] = "qhtable"


class Constant(ForcingBase):
    """Subclass for a .bc file [Forcing] block with constant value data."""

    function: Literal["constant"] = "constant"

    offset: float = Field(0.0, alias="offset")
    """float: All values in the table are increased by the offset (after multiplication by factor). Defaults to 0.0."""

    factor: float = Field(1.0, alias="factor")
    """float: All values in the table are multiplied with the factor. Defaults to 1.0."""


class ForcingGeneral(INIGeneral):
    """`[General]` section with .bc file metadata."""

    fileversion: str = Field("1.01", alias="fileVersion")
    """str: The file version."""

    filetype: Literal["boundConds"] = Field("boundConds", alias="fileType")


class ForcingModel(INIModel):
    """
    The overall model that contains the contents of one .bc forcings file.

    The `ForcingModel` class is the top-level model that aggregates metadata
    and multiple `[Forcing]` blocks. It provides functionality for parsing,
    serializing, and managing data within a .bc file.

    Attributes:
        general (ForcingGeneral):
            The `[General]` block containing metadata such as file version and type.
        forcing (List[ForcingBase]):
            A list of `[Forcing]` blocks representing the different forcings defined
            in the file.
        serializer_config (DataBlockINIBasedSerializerConfig):
            Configuration for serialization of the .bc file.

    Args:
        general (ForcingGeneral, optional):
            Metadata for the file. Defaults to an instance of `ForcingGeneral`.
        forcing (List[ForcingBase], optional, Defaults is []):
            A list of forcing definitions.
        serializer_config (DataBlockINIBasedSerializerConfig, optional):
            Serialization settings. Default to a predefined configuration.

    See Also:
        ForcingBase: Represents individual forcing blocks within the file.
        ForcingGeneral: Metadata model for the `[General]` section.

    Examples:
        Create a simple ForcingModel:
            ```python
            >>> from hydrolib.core.dflowfm.bc.models import ForcingModel, ForcingBase, ForcingGeneral, QuantityUnitPair
            >>> forcing_block = ForcingBase(
            ...     name="Location1",
            ...     function="timeseries",
            ...     quantityunitpair=[
            ...         QuantityUnitPair(quantity="waterlevel", unit="m")
            ...     ]
            ... )
            >>> model = ForcingModel(
            ...     general=ForcingGeneral(fileversion="1.01", filetype="boundConds"),
            ...     forcing=[forcing_block]
            ... )
            >>> print(model.general.fileversion)
            1.01
            >>> model.save(filepath="tests/data/output.bc") # doctest: +SKIP
            ```

        Parse a .bc file:
            ```python
            >>> from pathlib import Path
            >>> filepath = Path("tests/data/reference/bc/test.bc")
            >>> parsed_model = ForcingModel.parse(filepath)
            >>> print(parsed_model.keys())
            dict_keys(['general', 'forcing'])
            >>> print(len(parsed_model["forcing"]))
            6
            >>> print(parsed_model["forcing"][0]) # doctest: +SKIP
            {'_header': 'Forcing',
             'datablock': [['0.0000', '1.2300'],
              ['60.0000', '2.3400'],
              ['120.0000', '3.4500']],
             'name': 'boundary_timeseries',
             'function': 'timeseries',
             'timeinterpolation': 'block-To',
             'offset': '1.230',
             'factor': '2.340',
             'quantity': ['time', 'dischargebnd'],
             'unit': ['minutes since 2015-01-01 00:00:00', 'm³/s']}
            ```

        Serialize a ForcingModel:
            ```python
            >>> save_path = Path("output.bc")
            >>> model.save(filepath=save_path) # doctest: +SKIP
            >>> print(save_path.exists()) # doctest: +SKIP
            True
            ```

        Create a ForcingModel from a dictionary:
            ```python
            >>> from hydrolib.core.dflowfm.bc.models import ForcingModel
            >>> forcing_blocks_list = [
            ...     {
            ...         '_header': 'Forcing',
            ...         'datablock': [
            ...             ['0.0000', '1.2300'],
            ...             ['60.0000', '2.3400'],
            ...             ['120.0000', '3.4500']
            ...         ],
            ...         'name': 'boundary_timeseries',
            ...         'function': 'timeseries',
            ...         'timeinterpolation': 'block-To',
            ...         'offset': '1.230',
            ...         'factor': '2.340',
            ...         'quantity': ['time', 'dischargebnd'],
            ...         'unit': ['minutes since 2015-01-01 00:00:00', 'm³/s']
            ...     }
            ... ]
            >>> model_dict = {
            ...     "forcing": forcing_blocks_list,
            ...     "general": {"fileVersion": "1.01", "fileType": "boundConds"}
            ... }
            >>> model = ForcingModel(**model_dict)
            >>> print(len(model.forcing))
            1
            >>> type(model.forcing[0])
            <class 'hydrolib.core.dflowfm.bc.models.TimeSeries'>
            >>> print(model.general.fileversion)
            1.01

            ```

    Example .bc file content:
        ```.bc
        # written by HYDROLIB-core 0.3.0

        [General]
        fileVersion = 1.01
        fileType    = boundConds

        [Forcing]
        name               = boundary_timeseries
        function           = timeseries
        Time Interpolation = block-To
        offset             = 1.23
        factor             = 2.34
        quantity           = time
        unit               = minutes since 2015-01-01 00:00:00
        quantity           = dischargebnd
        unit               = m³/s
        0.0      1.23
        60.0     2.34
        120.0    3.45
        ```
    """

    general: ForcingGeneral = ForcingGeneral()
    """ForcingGeneral: `[General]` block with file metadata."""

    forcing: List[ForcingBase] = Field(default_factory=list)
    """List[ForcingBase]: List of `[Forcing]` blocks for all forcing
    definitions in a single .bc file. Actual data is stored in
    forcing[..].datablock from [hydrolib.core.dflowfm.ini.models.DataBlockINIBasedModel.datablock]."""

    _split_to_list = make_list_validator("forcing")

    serializer_config: DataBlockINIBasedSerializerConfig = (
        DataBlockINIBasedSerializerConfig(
            section_indent=0, property_indent=0, datablock_indent=0
        )
    )

    @classmethod
    def _ext(cls) -> str:
        """
        Get the file extension for .bc files.

        Returns:
            str: The file extension, ".bc".
        """
        return ".bc"

    @classmethod
    def _filename(cls) -> str:
        """
        Get the default filename for .bc files.

        Returns:
            str: The default filename, "boundaryconditions".
        """
        return "boundaryconditions"

    @classmethod
    def _get_parser(cls) -> Callable:
        """
        Retrieve the parser for .bc files.

        Returns:
            Callable: The parser function.
        """
        return cls.parse

    @classmethod
    def parse(cls, filepath: Path) -> Dict[str, Any]:
        """
        Parse a .bc file and create an instance of `ForcingModel`.

        Args:
            filepath (Path): The path to the .bc file.

        Returns:
            ForcingModel: The parsed model instance.
        """
        # It's odd to have to disable parsing something as comments
        # but also need to pass it to the *flattener*.
        # This method now only supports per model settings, not per section.
        parser = Parser(ParserConfig(parse_datablocks=True, parse_comments=False))

        with filepath.open(encoding="utf8") as f:
            for line in f:
                parser.feed_line(line)

        return parser.finalize().flatten(True, False)


class RealTime(StrEnum):
    """
    Enum class containing the valid value for the "realtime" reserved
    keyword for real-time controlled forcing data, e.g., for hydraulic
    structures.

    This class is used inside the ForcingData Union, to force detection
    of the realtime keyword, prior to considering it a filename.
    """

    realtime = "realtime"
    """str: Realtime data source, externally provided"""


ForcingData = Union[float, RealTime, ForcingModel]
"""Data type that selects from three different types of forcing data:
*   a scalar float constant
*   "realtime" keyword, indicating externally controlled.
*   A ForcingModel coming from a .bc file.
"""
