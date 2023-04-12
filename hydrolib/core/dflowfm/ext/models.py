from enum import Enum
from pathlib import Path
from typing import Dict, List, Literal, Optional, Union

from pydantic import Field, root_validator, validator

from hydrolib.core.basemodel import (
    DiskOnlyFileModel,
    validator_set_default_disk_only_file_model_when_none,
)
from hydrolib.core.dflowfm.bc.models import ForcingBase, ForcingData, ForcingModel
from hydrolib.core.dflowfm.ini.models import (
    INIBasedModel,
    INIGeneral,
    INIModel,
    INISerializerConfig,
)
from hydrolib.core.dflowfm.ini.serializer import INISerializerConfig
from hydrolib.core.dflowfm.ini.util import (
    LocationValidationConfiguration,
    get_enum_validator,
    get_split_string_on_delimiter_validator,
    make_list_validator,
    validate_location_specification,
)
from hydrolib.core.dflowfm.polyfile.models import PolyFile
from hydrolib.core.dflowfm.tim.models import TimModel
from hydrolib.core.utils import str_is_empty_or_none


class Boundary(INIBasedModel):
    """
    A `[Boundary]` block for use inside an external forcings file,
    i.e., a [ExtModel][hydrolib.core.dflowfm.ext.models.ExtModel].

    All lowercased attributes match with the boundary input as described in
    [UM Sec.C.5.2.1](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.5.2.1).
    """

    _disk_only_file_model_should_not_be_none = (
        validator_set_default_disk_only_file_model_when_none()
    )

    _header: Literal["Boundary"] = "Boundary"
    quantity: str = Field(alias="quantity")
    nodeid: Optional[str] = Field(alias="nodeId")
    locationfile: DiskOnlyFileModel = Field(
        default_factory=lambda: DiskOnlyFileModel(None), alias="locationFile"
    )
    forcingfile: ForcingModel = Field(alias="forcingFile")
    bndwidth1d: Optional[float] = Field(alias="bndWidth1D")
    bndbldepth: Optional[float] = Field(alias="bndBlDepth")

    def is_intermediate_link(self) -> bool:
        return True

    @classmethod
    def _is_valid_locationfile_data(
        cls, elem: Union[None, str, Path, DiskOnlyFileModel]
    ) -> bool:
        return isinstance(elem, Path) or (
            isinstance(elem, DiskOnlyFileModel) and elem.filepath is not None
        )

    @root_validator
    @classmethod
    def check_nodeid_or_locationfile_present(cls, values: Dict):
        """
        Verifies that either nodeid or locationfile properties have been set.

        Args:
            values (Dict): Dictionary with values already validated.

        Raises:
            ValueError: When none of the values are present.

        Returns:
            Dict: Validated dictionary of values for Boundary.
        """
        node_id = values.get("nodeid", None)
        location_file = values.get("locationfile", None)
        if str_is_empty_or_none(node_id) and not cls._is_valid_locationfile_data(
            location_file
        ):
            raise ValueError(
                "Either nodeId or locationFile fields should be specified."
            )
        return values

    def _get_identifier(self, data: dict) -> Optional[str]:
        """
        Retrieves the identifier for a boundary, which is the nodeid

        Args:
            data (dict): Dictionary of values for this boundary.

        Returns:
            str: The nodeid value or None if not found.
        """
        return data.get("nodeid")

    @property
    def forcing(self) -> ForcingBase:
        """Retrieves the corresponding forcing data for this boundary.

        Returns:
            ForcingBase: The corresponding forcing data. None when this boundary does not have a forcing file or when the data cannot be found.
        """

        if self.forcingfile is None:
            return None

        for forcing in self.forcingfile.forcing:

            if self.nodeid != forcing.name:
                continue

            for quantity in forcing.quantityunitpair:
                if quantity.quantity.startswith(self.quantity):
                    return forcing

        return None


class Lateral(INIBasedModel):
    """
    A `[Lateral]` block for use inside an external forcings file,
    i.e., a [ExtModel][hydrolib.core.dflowfm.ext.models.ExtModel].

    All lowercased attributes match with the lateral input as described in
    [UM Sec.C.5.2.2](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.5.2.2).
    """

    _header: Literal["Lateral"] = "Lateral"
    id: str = Field(alias="id")
    name: str = Field("", alias="name")
    locationtype: Optional[str] = Field(alias="locationType")
    nodeid: Optional[str] = Field(alias="nodeId")
    branchid: Optional[str] = Field(alias="branchId")
    chainage: Optional[float] = Field(alias="chainage")
    numcoordinates: Optional[int] = Field(alias="numCoordinates")
    xcoordinates: Optional[List[float]] = Field(alias="xCoordinates")
    ycoordinates: Optional[List[float]] = Field(alias="yCoordinates")
    discharge: ForcingData = Field(alias="discharge")

    def is_intermediate_link(self) -> bool:
        return True

    _split_to_list = get_split_string_on_delimiter_validator(
        "xcoordinates", "ycoordinates"
    )

    @root_validator(allow_reuse=True)
    def validate_that_location_specification_is_correct(cls, values: Dict) -> Dict:
        """Validates that the correct location specification is given."""
        return validate_location_specification(
            values, config=LocationValidationConfiguration(minimum_num_coordinates=1)
        )

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("id") or data.get("name")

    @validator("locationtype")
    @classmethod
    def validate_location_type(cls, v: str) -> str:
        """
        Method to validate whether the specified location type is correct.

        Args:
            v (str): Given value for the locationtype field.

        Raises:
            ValueError: When the value given for locationtype is unknown.

        Returns:
            str: Validated locationtype string.
        """
        possible_values = ["1d", "2d", "all"]
        if v.lower() not in possible_values:
            raise ValueError(
                "Value given ({}) not accepted, should be one of: {}".format(
                    v, ", ".join(possible_values)
                )
            )
        return v


class MeteoForcingFileType(str, Enum):
    """
    Enum class containing the valid values for the forcingFileType
    attribute in Meteo class.
    """

    bcascii = "bcAscii"
    """str: Space-uniform time series in <*.bc> file."""

    netcdf = "netcdf"
    """str: NetCDF, either with gridded data, or multiple station time series."""

    uniform = "uniform"
    """str: Space-uniform time series in <*.tim> file."""

    allowedvaluestext = "Possible values: bcAscii, netcdf, uniform."


class MeteoInterpolationMethod(str, Enum):
    """
    Enum class containing the valid values for the interpolationMethod
    attribute in Meteo class.
    """

    nearestnb = "nearestNb"
    """str: Nearest-neighbour interpolation, only with station-data in forcingFileType=netcdf"""

    allowedvaluestext = "Possible values: nearestNb (only with station data in forcingFileType=netcdf ). "


class Meteo(INIBasedModel):
    """
    A `[Meteo]` block for use inside an external forcings file,
    i.e., a [ExtModel][hydrolib.core.dflowfm.ext.models.ExtModel].

    All lowercased attributes match with the meteo input as described in
    [UM Sec.C.5.2.3](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#subsection.C.5.2.3).
    """

    class Comments(INIBasedModel.Comments):
        quantity: Optional[str] = Field(
            "Name of the quantity. See UM Section C.5.3", alias="quantity"
        )
        forcingfile: Optional[str] = Field(
            "Name of file containing the forcing for this meteo quantity.",
            alias="forcingFile",
        )
        forcingfiletype: Optional[str] = Field(
            "Type of forcingFile.", alias="forcingFileType"
        )
        targetmaskfile: Optional[str] = Field(
            "Name of <*.pol> file to be used as mask. Grid parts inside any polygon will receive the meteo forcing.",
            alias="targetMaskFile",
        )
        targetmaskinvert: Optional[str] = Field(
            "Flag indicating whether the target mask should be inverted, i.e., outside of all polygons: no or yes.",
            alias="targetMaskInvert",
        )
        interpolationmethod: Optional[str] = Field(
            "Type of (spatial) interpolation.", alias="interpolationMethod"
        )

    comments: Comments = Comments()

    _disk_only_file_model_should_not_be_none = (
        validator_set_default_disk_only_file_model_when_none()
    )

    _header: Literal["Meteo"] = "Meteo"
    quantity: str = Field(alias="quantity")
    forcingfile: Union[TimModel, ForcingModel, DiskOnlyFileModel] = Field(
        alias="forcingFile"
    )
    forcingfiletype: MeteoForcingFileType = Field(alias="forcingFileType")
    targetmaskfile: Optional[PolyFile] = Field(None, alias="targetMaskFile")
    targetmaskinvert: Optional[bool] = Field(None, alias="targetMaskInvert")
    interpolationmethod: Optional[MeteoInterpolationMethod] = Field(
        alias="interpolationMethod"
    )

    def is_intermediate_link(self) -> bool:
        return True

    forcingfiletype_validator = get_enum_validator(
        "forcingfiletype", enum=MeteoForcingFileType
    )
    interpolationmethod_validator = get_enum_validator(
        "interpolationmethod", enum=MeteoInterpolationMethod
    )


class ExtGeneral(INIGeneral):
    """The external forcing file's `[General]` section with file meta data."""

    _header: Literal["General"] = "General"
    fileversion: str = Field("2.01", alias="fileVersion")
    filetype: Literal["extForce"] = Field("extForce", alias="fileType")


class ExtModel(INIModel):
    """
    The overall external forcings model that contains the contents of one external forcings file (new format).

    This model is typically referenced under a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.external_forcing.extforcefilenew`.

    Attributes:
        general (ExtGeneral): `[General]` block with file metadata.
        boundary (List[Boundary]): List of `[Boundary]` blocks for all boundary conditions.
        lateral (List[Lateral]): List of `[Lateral]` blocks for all lateral discharges.
        meteo (List[Meteo]): List of `[Meteo]` blocks for all meteorological forcings.
    """

    general: ExtGeneral = ExtGeneral()
    boundary: List[Boundary] = []
    lateral: List[Lateral] = []
    meteo: List[Meteo] = []
    serializer_config: INISerializerConfig = INISerializerConfig(
        section_indent=0, property_indent=0
    )
    _split_to_list = make_list_validator("boundary", "lateral", "meteo")

    @classmethod
    def _ext(cls) -> str:
        return ".ext"

    @classmethod
    def _filename(cls) -> str:
        return "bnd"
