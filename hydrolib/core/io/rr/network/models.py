from typing import Callable, List, Optional

from pydantic.fields import Field

from hydrolib.core.basemodel import BaseModel, FileModel
from hydrolib.core.io.base import DummmyParser, DummySerializer


class Node(BaseModel):
    """Represents a node from the topology node file."""

    id: str = Field(alias="id")
    name: str = Field(alias="nm")
    branchid: int = Field(alias="ri")
    modelnodetype: int = Field(alias="mt")
    netternodetype: int = Field(alias="nt")
    objectid: str = Field(alias="ObId")
    xposition: float = Field(alias="px")
    yposition: float = Field(alias="py")

    def _get_identifier(self, data: dict) -> Optional[str]:
        return data["id"] if "id" in data else data.get("nm")


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
        return DummySerializer.serialize

    @classmethod
    def _get_parser(cls) -> Callable:
        return DummmyParser.parse
