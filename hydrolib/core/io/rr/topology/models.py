from typing import Callable, List, Optional

from pydantic.class_validators import root_validator
from pydantic.fields import Field

from hydrolib.core.basemodel import BaseModel, FileModel
from hydrolib.core.io.base import DummmyParser, DummySerializer
from hydrolib.core.io.net.models import Network
from hydrolib.core.io.rr.topology.parser import NetworkTopologyFileParser
from hydrolib.core.io.rr.topology.serializer import (
    LinkFileSerializer,
    NodeFileSerializer,
)

# Dictionary with `nt` mapped against the expected `mt`.
nodetypes_netter_to_rr = {
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
    name: Optional[str] = Field(alias="nm")
    branchid: int = Field(alias="ri")
    modelnodetype: int = Field(alias="mt")
    netternodetype: int = Field(alias="nt")
    objectid: str = Field(alias="ObID")
    xposition: float = Field(alias="px")
    yposition: float = Field(alias="py")

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("id") or data.get("nm")

    def dict(self, *args, **kwargs):
        kwargs["by_alias"] = True
        return super().dict(*args, **kwargs)

    @root_validator()
    @classmethod
    def _validate_node_type(cls, values):

        cls._raise_if_invalid_type(
            values,
            "modelnodetype",
            set(nodetypes_netter_to_rr.values()),
            "model node type (mt)",
        )

        modelnodetype = values.get("modelnodetype")

        # modelnodetype=6 ("boundary node") is a special case that allows various netter nodetypes,
        # so therefore it always validates well.
        if modelnodetype == 6:
            return values

        cls._raise_if_invalid_type(
            values,
            "netternodetype",
            set(nodetypes_netter_to_rr.keys()),
            "netter node type (nt)",
        )

        netternodetype = values.get("netternodetype")
        modelnodetype_expected = nodetypes_netter_to_rr[netternodetype]

        if modelnodetype != modelnodetype_expected:
            raise ValueError(
                f"{modelnodetype} is not a supported model node type (mt) when netter node type (nt) is {netternodetype}. Supported value: {modelnodetype_expected}."
            )

        return values

    @classmethod
    def _raise_if_invalid_type(
        cls, values, field_name: str, supported_values: set, description: str
    ):
        """Validates the node type for the provided `field_name`.
        The specified node type should contain a supported value,
        otherwise a `ValueError` is raised.


        Args:
            values ([type]): Dictionary with values that are used to create this `Node`.
            field_name (str): Field name of the node type to validate.
            supported_values (set): Set of all the supported values for this node type.
            description (str): Description of this node type that will be readable for the user.

        Raises:
            ValueError: Thrown when `supported_values` does node contain the node type.
        """
        field_value = values.get(field_name)

        if field_value not in supported_values:
            str_supported_values = ", ".join([str(t) for t in supported_values])
            raise ValueError(
                f"{field_value} is not a supported {description}. Supported values: {str_supported_values}."
            )


class NodeFile(FileModel):
    """Represents the file with the RR node topology data."""

    _parser = NetworkTopologyFileParser(enclosing_tag="node")
    node: List[Node] = Field([], alias="node")

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
        return cls._parser.parse


class Link(BaseModel):
    """Represents a link from the topology link file."""

    id: str = Field(alias="id")
    name: Optional[str] = Field(alias="nm")
    branchid: int = Field(alias="ri")
    modellinktype: int = Field(alias="mt")
    branchtype: int = Field(alias="bt")
    objectid: str = Field(alias="ObID")
    beginnode: str = Field(alias="bn")
    endnode: str = Field(alias="en")

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data.get("id") or data.get("nm")

    def dict(self, *args, **kwargs):
        kwargs["by_alias"] = True
        return super().dict(*args, **kwargs)


class LinkFile(FileModel):
    """Represents the file with the RR link topology data."""

    _parser = NetworkTopologyFileParser(enclosing_tag="brch")
    link: List[Link] = Field([], alias="brch")

    @classmethod
    def _ext(cls) -> str:
        return ".tp"

    @classmethod
    def _filename(cls) -> str:
        return "3b_link"

    @classmethod
    def _get_serializer(cls) -> Callable:
        return LinkFileSerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable:
        return cls._parser.parse
