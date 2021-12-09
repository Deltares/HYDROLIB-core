from enum import Enum
from typing import List, Literal, Optional

from pydantic.fields import Field

from hydrolib.core.io.ini.models import INIBasedModel, INIGeneral


class NodeType(str, Enum):
    inspection = "inspection"
    soakawaydrain = "soakawayDrain"
    compartment = "compartment"
    unspecified = "unspecified"


class StorageType(str, Enum):
    reservoir = "reservoir"
    closed = "closed"


class Interpolate(str, Enum):
    linear = "linear"
    block = "block"


class StorageNodeGeneral(INIGeneral):
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
            "Connection node on which the storage nodeis located.", alias="nodeId"
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
            "Interpolation type for storage area table either linear or block.",
            alias="interpolate",
        )

    comments: Comments = Comments()
    _header: Literal["StorageNode"] = "StorageNode"
    id: str = Field(alias="id")
    name: str = Field(alias="name")
    manholeid: Optional[str] = Field(alias="manholeId")

    nodetype: Optional[NodeType] = Field(NodeType.unspecified, alias="nodeType")
    nodeid: str = Field(alias="nodeId")
    usetable: bool = Field(alias="useTable")

    # useTable is True
    bedlevel: float = Field(alias="bedLevel")
    area: float = Field(alias="area")
    streetlevel: float = Field(alias="streetLevel")
    streetstoragearea: float = Field(alias="streetStorageArea")
    storagetype: Optional[StorageType] = Field(
        StorageType.reservoir, alias="storageType"
    )

    # useTable is False
    numlevels: int = Field(alias="numLevels")
    levels: List[float] = Field(alias="levels")
    storagearea: List[float] = Field(alias="storageArea")
    interpolate: Optional[Interpolate] = Field(Interpolate.linear, alias="interpolate")
