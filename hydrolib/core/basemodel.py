from typing import Protocol, Optional, List, Union, Type, Any
from pydantic import BaseModel as PydanticBaseModel
from pydantic import FilePath, validator
from .utils import get_model_type_from_union
from pathlib import Path


class RootModel(Protocol):
    """
    A Root Model probably has some children
    but the root manages them. Like a MDU that
    knows about the relations between geometry
    and other objects.
    """

    def copy(self, DirectoryPath) -> None:
        pass

    def validate(self) -> None:
        pass


class BaseModel(PydanticBaseModel):
    class Config:
        arbitrary_types_allowed = True
        validate_assignment = True
        use_enum_values = True
        extra = "allow"


class FileModel(BaseModel):
    """Base class to represent models with a file representation."""

    # TODO Some logic that if such a thing is
    # initialised (from a string/filepath) it will work.
    # but also when you call serialize, a name should be generated?

    filepath: Optional[FilePath] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.filepath:
            self.fill()

    @classmethod
    def validate(cls: Type["FileModel"], value: Any) -> "FileModel":
        # Enable initialization with a Path
        if isinstance(value, Path):
            value = {"filepath": value}
        return super().validate(value)

    @classmethod
    def parse(cls, filepath: FilePath):
        # cls.get_parser().parse(filepath)  # actual implementation
        return cls(filepath=filepath)

    def fill(self):
        """Update instance based on parsing the filepath"""
        # parsemethod(self.filepath)
        pass


class Edge(BaseModel):
    a: int = 0
    b: int = 1


class Network(FileModel):
    n_vertices: int = 100
    edges: List[Edge] = [Edge()]


class FMModel(FileModel):
    name: str = "Dummy"
    network: Optional[Network]


class DIMR(FileModel):
    model: Optional[FMModel]
