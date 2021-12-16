from enum import Enum
from typing import List, Literal, Optional

from pydantic.class_validators import root_validator, validator
from pydantic.fields import Field

from hydrolib.core.io.ini.models import INIBasedModel, INIGeneral, INIModel
from hydrolib.core.io.ini.util import (
    get_enum_validator,
    get_required_fields_validator,
    get_split_string_on_delimiter_validator,
    make_list_length_root_validator,
    make_list_validator,
)


class NodeType(str, Enum):
    """
    Enum class containing the valid values for the node type
    as used in StorageNode.
    """

    inspection = "inspection"
    soakawaydrain = "soakawayDrain"
    compartment = "compartment"
    unspecified = "unspecified"


class StorageType(str, Enum):
    """
    Enum class containing the valid values for the storage type
    as used in StorageNode.
    """

    reservoir = "reservoir"
    closed = "closed"


class Interpolation(str, Enum):
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
    [UM Sec.C.17](https://content.oss.deltares.nl/delft3d/manuals/D-Flow_FM_User_Manual_1D2D.pdf#section.C.17).
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
    manholeid: Optional[str] = Field(alias="manholeId")

    nodetype: Optional[NodeType] = Field(NodeType.unspecified.value, alias="nodeType")
    nodeid: str = Field(alias="nodeId")
    usetable: bool = Field(alias="useTable")

    # useTable is True
    bedlevel: Optional[float] = Field(alias="bedLevel")
    area: Optional[float] = Field(alias="area")
    streetlevel: Optional[float] = Field(alias="streetLevel")
    streetstoragearea: Optional[float] = Field(alias="streetStorageArea")
    storagetype: Optional[StorageType] = Field(
        StorageType.reservoir.value, alias="storageType"
    )

    # useTable is False
    numlevels: Optional[int] = Field(alias="numLevels")
    levels: Optional[List[float]] = Field(alias="levels")
    storagearea: Optional[List[float]] = Field(alias="storageArea")
    interpolate: Optional[Interpolation] = Field(
        Interpolation.linear.value, alias="interpolate"
    )

    _interpolation_validator = get_enum_validator("interpolate", enum=Interpolation)
    _nodetype_validator = get_enum_validator("nodetype", enum=NodeType)
    _storagetype_validator = get_enum_validator("storagetype", enum=StorageType)
    _split_to_list = get_split_string_on_delimiter_validator(
        "levels",
        "storagearea",
        delimiter=" ",
    )

    _check_list_length = make_list_length_root_validator(
        "levels",
        "storagearea",
        length_name="numlevels",
        list_required_with_length=True,
    )

    _usetable_true_validator = get_required_fields_validator(
        "numlevels",
        "levels",
        "storagearea",
        conditional_field_name="usetable",
        conditional_value=True,
    )

    _usetable_false_validator = get_required_fields_validator(
        "bedlevel",
        "area",
        "streetlevel",
        conditional_field_name="usetable",
        conditional_value=False,
    )

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("id") or data.get("name")


class StorageNodeModel(INIModel):
    """
    The overall storage node model that contains the contents of one storage node file.

    This model is typically referenced under a [FMModel][hydrolib.core.io.mdu.models.FMModel]`.geometry.storagenodefile[..]`.

    Attributes:
        general (StorageNodeGeneral): `[General]` block with file metadata.
        storagenode (List[StorageNode]): List of `[StorageNode]` blocks for all storage nodes.
    """

    general: StorageNodeGeneral = StorageNodeGeneral()
    storagenode: List[StorageNode] = []

    _make_list = make_list_validator("storagenode")

    @classmethod
    def _filename(cls) -> str:
        return "nodeFile"

    @validator("storagenode", each_item=True)
    def _validate(cls, storagenode: StorageNode, values: dict):
        """Validates for each storage node whether the streetStorageArea value is provided
        when the general useStreetStorage is True and the storage node useTable is False.
        """

        usestreetstorage = values["general"].usestreetstorage

        if (
            usestreetstorage
            and not storagenode.usetable
            and storagenode.streetstoragearea is None
        ):
            raise ValueError(
                f"streetStorageArea should be provided when useStreetStorage is True and useTable is False for storage node with id {storagenode.id}"
            )

        return storagenode
