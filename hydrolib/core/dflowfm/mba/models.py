"""Mass balance area model definitions for D-Flow FM.

A mass balance area file (``<*_mba.ini>``) defines polygons in the model domain for which mass balance
output is produced during a run. The polygons subdivide the domain into regions; the model then writes
timeseries of mass balances per region and the cumulative fluxes between adjacent regions.

The file is referenced from the MDU ``[output]`` section via the ``mbaFile`` keyword (a space-separated
list of files). See the D-Flow FM 1D2D User Manual, Appendix F.2.5.
"""

from typing import Annotated, Literal

from pydantic import BeforeValidator, Field, model_validator

from hydrolib.core.base.models import (
    DiskOnlyFileModel,
    set_default_disk_only_file_model,
)
from hydrolib.core.dflowfm.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.dflowfm.ini.util import make_list
from hydrolib.core.dflowfm.validators import CoordinateValidator


class MassBalanceAreaGeneral(INIGeneral):
    """The mass balance area file's `[General]` section with file meta data.

    Examples:
        - The default general block reports the fixed version and file type:
            ```python
            >>> from hydrolib.core.dflowfm.mba.models import MassBalanceAreaGeneral
            >>> general = MassBalanceAreaGeneral()
            >>> general.fileversion
            '1.00'
            >>> general.filetype
            'massBalanceAreas'

            ```

    See Also:
        MassBalanceAreaModel: Top-level model that owns this `[General]` block.
    """

    class Comments(INIBasedModel.Comments):
        """Comments for the MassBalanceAreaGeneral section fields."""

        fileversion: str | None = Field(
            "File version. Do not edit this.", alias="fileVersion"
        )
        filetype: str | None = Field(
            "File type. Should be 'massBalanceAreas'. Do not edit this.",
            alias="fileType",
        )

    comments: Comments = Comments()
    _header: Literal["General"] = "General"
    fileversion: str = Field("1.00", alias="fileVersion")
    filetype: Literal["massBalanceAreas"] = Field("massBalanceAreas", alias="fileType")


class MassBalanceArea(CoordinateValidator, INIBasedModel):
    """A single mass balance area included in the mass balance area file.

    The area polygon is defined either by a separate polygon file (`locationFile`) or by specifying the
    polygon coordinates directly (`numCoordinates`, `xCoordinates`, `yCoordinates`). Exactly one of these
    two forms must be supplied.

    All lowercased attributes match the mass balance area input as described in the D-Flow FM 1D2D
    User Manual, Appendix F.2.5.

    Examples:
        - Define an area by a separate polygon file:
            ```python
            >>> from hydrolib.core.dflowfm.mba.models import MassBalanceArea
            >>> area = MassBalanceArea(name="EstruaryWest", locationFile="EstruaryWest.pol")
            >>> area.name
            'EstruaryWest'
            >>> area.locationfile.filepath.name
            'EstruaryWest.pol'

            ```
        - Define an area by inline polygon coordinates:
            ```python
            >>> from hydrolib.core.dflowfm.mba.models import MassBalanceArea
            >>> area = MassBalanceArea(
            ...     name="triangle",
            ...     numCoordinates=3,
            ...     xCoordinates=[0.0, 1.0, 2.0],
            ...     yCoordinates=[0.0, 1.0, 0.0],
            ... )
            >>> area.numcoordinates
            3
            >>> area.xcoordinates
            [0.0, 1.0, 2.0]

            ```

    See Also:
        MassBalanceAreaModel: Top-level model that holds a list of these areas.
    """

    class Comments(INIBasedModel.Comments):
        """Comments for the MassBalanceArea section fields."""

        name: str | None = "Name of the mass balance area (max. 255 characters)."
        locationfile: str | None = Field(
            "(optional) Name of mass balance area polygon (*.pol).",
            alias="locationFile",
        )
        numcoordinates: str | None = Field(
            "(optional) Number of values in xCoordinates and yCoordinates. "
            "This value should be greater than or equal to 3.",
            alias="numCoordinates",
        )
        xcoordinates: str | None = Field(
            "(optional) x-coordinates of the mass balance area polygon. "
            "(number of values = numCoordinates)",
            alias="xCoordinates",
        )
        ycoordinates: str | None = Field(
            "(optional) y-coordinates of the mass balance area polygon. "
            "(number of values = numCoordinates)",
            alias="yCoordinates",
        )

    comments: Comments = Comments()
    _header: Literal["MassBalanceArea"] = "MassBalanceArea"
    name: str = Field(max_length=255, alias="name")
    locationfile: Annotated[
        DiskOnlyFileModel, BeforeValidator(set_default_disk_only_file_model)
    ] = Field(default_factory=lambda: DiskOnlyFileModel(None), alias="locationFile")
    numcoordinates: int | None = Field(None, alias="numCoordinates")
    xcoordinates: list[float] | None = Field(None, alias="xCoordinates")
    ycoordinates: list[float] | None = Field(None, alias="yCoordinates")

    @model_validator(mode="after")
    def _validate_location_specification(self) -> "MassBalanceArea":
        """Validate that exactly one valid location form is supplied.

        A mass balance area is defined either by `locationFile` or by the coordinate triple
        (`numCoordinates`, `xCoordinates`, `yCoordinates`). When coordinates are used, all three must be
        present, the coordinate lists must match `numCoordinates`, and at least 3 coordinates are required
        (a polygon).

        Raises:
            ValueError: If neither or both location forms are supplied, if the coordinate form is
                incomplete, if the coordinate counts do not match, or if fewer than 3 coordinates
                are given.
        """
        has_location_file = (
            self.locationfile is not None and self.locationfile.filepath is not None
        )
        # (locationfile is always a DiskOnlyFileModel; an unset value has filepath=None)
        has_num = self.numcoordinates is not None
        has_x = self.xcoordinates is not None
        has_y = self.ycoordinates is not None
        has_coordinates = has_num or has_x or has_y

        if has_location_file and has_coordinates:
            raise ValueError(
                "A MassBalanceArea must specify either locationFile or "
                "numCoordinates/xCoordinates/yCoordinates, not both."
            )
        if not has_location_file and not has_coordinates:
            raise ValueError(
                "A MassBalanceArea must specify either locationFile or "
                "numCoordinates/xCoordinates/yCoordinates."
            )
        if has_coordinates and not (has_num and has_x and has_y):
            raise ValueError(
                "A MassBalanceArea defined by coordinates must specify "
                "numCoordinates, xCoordinates and yCoordinates together."
            )
        if has_coordinates and not (
            self.numcoordinates == len(self.xcoordinates) == len(self.ycoordinates)
        ):
            raise ValueError(
                "numCoordinates should be equal to the number of xCoordinates and yCoordinates."
            )
        if has_coordinates and self.numcoordinates < 3:
            raise ValueError(
                "A MassBalanceArea polygon should have at least 3 coordinates."
            )
        return self

    def _get_identifier(self, data: dict) -> str | None:
        return data.get("name")


class MassBalanceAreaModel(INIModel):
    """The overall model that contains the contents of one mass balance area file (`<*_mba.ini>`).

    This model is typically referenced from the MDU `[output]` section via the `mbaFile` keyword.

    Attributes:
        general (MassBalanceAreaGeneral): `[General]` block with file metadata.
        massbalancearea (list[MassBalanceArea]): List of `[MassBalanceArea]` blocks, one per area.

    Examples:
        - Build a model with two areas and inspect them:
            ```python
            >>> from hydrolib.core.dflowfm.mba.models import MassBalanceArea, MassBalanceAreaModel
            >>> model = MassBalanceAreaModel(
            ...     massbalancearea=[
            ...         MassBalanceArea(name="EstruaryWest", locationFile="EstruaryWest.pol"),
            ...         MassBalanceArea(name="River", locationFile="River.pol"),
            ...     ]
            ... )
            >>> [area.name for area in model.massbalancearea]
            ['EstruaryWest', 'River']
            >>> model.general.filetype
            'massBalanceAreas'

            ```
        - An empty model has the fixed file type and no areas:
            ```python
            >>> from hydrolib.core.dflowfm.mba.models import MassBalanceAreaModel
            >>> model = MassBalanceAreaModel()
            >>> model.general.filetype
            'massBalanceAreas'
            >>> model.massbalancearea
            []

            ```

    See Also:
        MassBalanceArea: A single `[MassBalanceArea]` block.
        MassBalanceAreaGeneral: The `[General]` metadata block.
    """

    general: MassBalanceAreaGeneral = MassBalanceAreaGeneral()
    massbalancearea: Annotated[list[MassBalanceArea], BeforeValidator(make_list)] = []

    @classmethod
    def _filename(cls) -> str:
        return "mba"
