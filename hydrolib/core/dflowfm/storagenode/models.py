from typing import Annotated, List, Literal, Optional

from pydantic import (
    BeforeValidator,
    Field,
    ValidationInfo,
    field_validator,
    model_validator,
)
from strenum import StrEnum

from hydrolib.core.dflowfm.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.dflowfm.ini.util import (
    UnknownKeywordErrorManager,
    enum_value_parser,
    make_list,
    split_string_on_delimiter,
    validate_correct_length,
    validate_required_fields,
)


class NodeType(StrEnum):
    """
    Enum class containing the valid values for the node type
    as used in StorageNode.
    """

    inspection = "inspection"
    soakawaydrain = "soakawayDrain"
    compartment = "compartment"
    unspecified = "unspecified"


class StorageType(StrEnum):
    """
    Enum class containing the valid values for the storage type
    as used in StorageNode.
    """

    reservoir = "reservoir"
    closed = "closed"


class Interpolation(StrEnum):
    """
    Enum class containing the valid values for the interpolation type
    as used for a storage area table in StorageNode.
    """

    linear = "linear"
    block = "block"


class StorageNodeGeneral(INIGeneral):
    """The storage node file's `[General]` section with file meta data."""

    class Comments(INIBasedModel.Comments):
        fileversion: Optional[str] = Field(
            "File version. Do not edit this.", alias="fileVersion"
        )
        filetype: Optional[str] = Field(
            "File type. Should be 'storageNodes'. Do not edit this.",
            alias="fileType",
        )
        usestreetstorage: Optional[str] = Field(
            "Indicates whether above streetLevel the streetStorageArea must be used (true) "
            + "or the regular storage area continues (false). This option is only applicable "
            + "for storage nodes with useTable = false.",
            alias="useStreetStorage",
        )

    comments: Comments = Comments()
    _header: Literal["General"] = "General"
    fileversion: str = Field("2.00", alias="fileVersion")
    filetype: Literal["storageNodes"] = Field("storageNodes", alias="fileType")
    usestreetstorage: Optional[bool] = Field(True, alias="useStreetStorage")


class StorageNode(INIBasedModel):
    """
    A storage node that is included in the storage node file.

    All lowercased attributes match with the storage node input as described in
    [UM Sec.C.17](https://content.oss.deltares.nl/delft3dfm1d2d/D-Flow_FM_User_Manual_1D2D.pdf#section.C.17).
    """

    class Comments(INIBasedModel.Comments):
        id: Optional[str] = Field("Unique id of the storage node.", alias="id")
        name: Optional[str] = Field("Long name in the user interface.", alias="name")
        manholeid: Optional[str] = Field(
            "(optional) Unique id of manhole that this (compartment) node is part of.",
            alias="manholeId",
        )
        nodetype: Optional[str] = Field(
            "(optional) Type of the node. Possible values are: "
            + "inspection: inspection chamber, "
            + "soakawayDrain: soakaway drain (infiltration), "
            + "compartment: manhole compartment, "
            + "unspecified: general storage node of unspecified type",
            alias="nodeType",
        )
        nodeid: Optional[str] = Field(
            "Connection node on which the storage node is located.", alias="nodeId"
        )
        usetable: Optional[str] = Field(
            "Switch to select a simple (false) or tabulated (true) storage area.",
            alias="useTable",
        )
        bedlevel: Optional[str] = Field(
            "Bed level of the storage area [m AD].", alias="bedLevel"
        )
        area: Optional[str] = Field(
            "Storage area from bedLevel up to streetLevel (and beyond if useStreetStorage = false) [m2].",
            alias="area",
        )
        streetlevel: Optional[str] = Field(
            "Street level of the storage area [m AD].", alias="streetLevel"
        )
        streetstoragearea: Optional[str] = Field(
            "Storage area from streetLevel upwards if useStreetStorage = true [m2].",
            alias="streetStorageArea",
        )
        storagetype: Optional[str] = Field(
            "Possible values: "
            + "reservoir: Above streetLevel the storage area of this node is also taken into account. "
            + "closed: Above streetLevel this storage node has no storage area.",
            alias="storageType",
        )
        numlevels: Optional[str] = Field(
            "Number of levels in storage area table.", alias="numLevels"
        )
        levels: Optional[str] = Field(
            "Levels in storage area table [m].", alias="levels"
        )
        storagearea: Optional[str] = Field(
            "Areas in storage area table [m2].", alias="storageArea"
        )
        interpolate: Optional[str] = Field(
            "Interpolation type for storage area table. Possible values: linear or block.",
            alias="interpolate",
        )

    comments: Comments = Comments()
    _header: Literal["StorageNode"] = "StorageNode"
    id: str = Field(alias="id")
    name: str = Field(alias="name")
    manholeid: Optional[str] = Field(None, alias="manholeId")

    nodetype: Optional[NodeType] = Field(NodeType.unspecified.value, alias="nodeType")
    nodeid: str = Field(alias="nodeId")
    usetable: bool = Field(alias="useTable")

    # useTable is True
    bedlevel: Optional[float] = Field(None, alias="bedLevel")
    area: Optional[float] = Field(None, alias="area")
    streetlevel: Optional[float] = Field(None, alias="streetLevel")
    streetstoragearea: Optional[float] = Field(None, alias="streetStorageArea")
    storagetype: Optional[StorageType] = Field(
        StorageType.reservoir.value, alias="storageType"
    )

    # useTable is False
    numlevels: Optional[int] = Field(None, alias="numLevels")
    levels: Optional[List[float]] = Field(None, alias="levels")
    storagearea: Optional[List[float]] = Field(None, alias="storageArea")
    interpolate: Optional[Interpolation] = Field(
        Interpolation.linear.value, alias="interpolate"
    )

    @classmethod
    def _get_unknown_keyword_error_manager(cls) -> Optional[UnknownKeywordErrorManager]:
        """
        The StorageNode does not currently support raising an error on unknown keywords.
        """
        return None

    @field_validator("interpolate", mode="before")
    @classmethod
    def _interpolate_validator(cls, v) -> Interpolation:
        return enum_value_parser(v, Interpolation)

    @field_validator("nodetype", mode="before")
    @classmethod
    def _nodetype_validator(cls, v) -> NodeType:
        return enum_value_parser(v, NodeType)

    @field_validator("storagetype", mode="before")
    @classmethod
    def _storagetype_validator(cls, v) -> StorageType:
        return enum_value_parser(v, StorageType)

    @field_validator("levels", "storagearea", mode="before")
    @classmethod
    def _split_to_list(cls, v, info: ValidationInfo) -> List[float]:
        return split_string_on_delimiter(cls, v, info)

    @model_validator(mode="after")
    @classmethod
    def check_list_length_levels(cls, values: "StorageNode") -> "StorageNode":
        """Validates that the length of the levels field is as expected."""
        validate_correct_length(
            values.model_dump(),
            "levels",
            "storagearea",
            length_name="numlevels",
            list_required_with_length=True,
        )
        return values

    @model_validator(mode="after")
    @classmethod
    def validate_that_required_fields_are_present_when_using_tables(
        cls, values: "StorageNode"
    ) -> "StorageNode":
        """Validates that the specified fields are present when the usetable field is also present."""
        validate_required_fields(
            values.model_dump(),
            "numlevels",
            "levels",
            "storagearea",
            conditional_field_name="usetable",
            conditional_value=True,
        )
        return values

    @model_validator(mode="after")
    @classmethod
    def validate_that_required_fields_are_present_when_not_using_tables(
        cls, values: "StorageNode"
    ) -> "StorageNode":
        """Validates that the specified fields are present."""
        validate_required_fields(
            values.model_dump(),
            "bedlevel",
            "area",
            "streetlevel",
            conditional_field_name="usetable",
            conditional_value=False,
        )
        return values

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("id") or data.get("name")


class StorageNodeModel(INIModel):
    """
    The overall storage node model that contains the contents of one storage node file.

    This model is typically referenced under a [FMModel][hydrolib.core.dflowfm.mdu.models.FMModel]`.geometry.storagenodefile[..]`.

    Attributes:
        general (StorageNodeGeneral): `[General]` block with file metadata.
        storagenode (List[StorageNode]): List of `[StorageNode]` blocks for all storage nodes.
    """

    general: StorageNodeGeneral = StorageNodeGeneral()
    storagenode: Annotated[List[StorageNode], BeforeValidator(make_list)] = []

    @classmethod
    def _filename(cls) -> str:
        return "nodeFile"

    @field_validator("storagenode", mode="after")
    def _validate(cls, storagenodes: List[StorageNode], info: ValidationInfo):
        """Validates for each storage node whether the streetStorageArea value is provided
        when the general useStreetStorage is True and the storage node useTable is False.
        """

        usestreetstorage = info.data["general"].usestreetstorage

        for storagenode in storagenodes:
            if (
                usestreetstorage
                and not storagenode.usetable
                and storagenode.streetstoragearea is None
            ):
                raise ValueError(
                    f"streetStorageArea should be provided when useStreetStorage is True and useTable is False for storage node with id {storagenode.id}"
                )

        return storagenodes
