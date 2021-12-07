from typing import Callable, List, Optional

from pydantic.class_validators import root_validator
from pydantic.fields import Field

from hydrolib.core.basemodel import BaseModel, FileModel
from hydrolib.core.io.rr.network.parser import NodeFileParser
from hydrolib.core.io.rr.network.serializer import NodeFileSerializer

# Dictionary with `nt` mapped against the expected `mt`.
nodetypes = {
    43: 1,
    44: 2,
    45: 3,
    46: 4,
    None: 5,
    34: 6,
    35: 6,
    47: 6,
    48: 8,
    49: 9,
    50: 10,
    51: 11,
    52: 12,
    56: 14,
    55: 15,
    54: 16,
    69: 23,
}


class Node(BaseModel):
    """Represents a node from the topology node file."""

    id: str = Field(alias="id")
    name: str = Field(alias="nm")
    branchid: int = Field(alias="ri")
    modelnodetype: int = Field(alias="mt")
    netternodetype: int = Field(alias="nt")
    objectid: str = Field(alias="ObID")
    xposition: float = Field(alias="px")
    yposition: float = Field(alias="py")

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data["id"] if "id" in data else data.get("nm")

    def dict(self, *args, **kwargs):
        kwargs["by_alias"] = True
        return super().dict(*args, **kwargs)

    @root_validator()
    @classmethod
    def _valdate_node_type(cls, values):

        cls._raise_if_invalid_type(
            values, "modelnodetype", set(nodetypes.values()), "model node type (mt)"
        )

        modelnodetype = values.get("modelnodetype")
        if modelnodetype == 6:
            return values

        cls._raise_if_invalid_type(
            values, "netternodetype", set(nodetypes.keys()), "netter node type (nt)"
        )

        netternodetype = values.get("netternodetype")
        modelnodetype_expected = nodetypes[netternodetype]

        if modelnodetype != modelnodetype_expected:
            raise ValueError(
                f"{modelnodetype} is not a supported model node type (mt) when netter node type (nt) is {netternodetype}. Supported value: {modelnodetype_expected}."
            )

        return values

    @classmethod
    def _raise_if_invalid_type(
        cls, values, field_name: str, supported_values: set, description: str
    ):
        type = values.get(field_name)

        if type not in supported_values:
            str_supported_values = ", ".join([str(t) for t in supported_values])
            raise ValueError(
                f"{type} is not a supported {description}. Supported values: {str_supported_values}."
            )


class NodeFile(FileModel):
    node: List[Node] = []

    @classmethod
    def _ext(cls) -> str:
        return ".tp"

    @classmethod
    def _filename(cls) -> str:
        return "3b_nod"

    @classmethod
    def _get_serializer(cls) -> Callable:
        return NodeFileSerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable:
        return NodeFileParser.parse
