from pathlib import Path
from typing import Dict, List
from unittest.mock import MagicMock

from hydrolib.core.base.models import BaseModel, ParsableFileModel
from hydrolib.core.base.parser import DummmyParser
from hydrolib.core.base.serializer import DummySerializer


# Common test model classes to reduce duplication
class SimpleTestModel(BaseModel):
    """A simple test model with basic properties."""

    name: str
    value: int


class ModelWithLinks(BaseModel):
    """A test model that overrides link methods."""

    name: str

    def is_file_link(self) -> bool:
        return True

    def is_intermediate_link(self) -> bool:
        return True


class ChildTestModel(ModelWithLinks):
    """A child test model for hierarchy testing."""

    value: int


class ParentTestModel(ModelWithLinks):
    """A parent test model for hierarchy testing."""

    child: ChildTestModel
    children: List[ChildTestModel] = []


class BaseModelWithFunc(BaseModel):
    """A test base model that can track function calls."""

    def test_func(self):
        """Test function that can be used to track calls."""
        pass


class ChildModelWithFunc(BaseModelWithFunc, ChildTestModel):
    """A child model that includes the test_func method."""

    pass


class ParentModelWithFunc(BaseModelWithFunc, ParentTestModel):
    """A parent model that includes the test_func method."""

    pass


# Common test model classes for ParsableFileModel tests
class ParsableModelBase(ParsableFileModel):
    """Base class for parsable file model tests with common structure."""

    name: str = "default"
    value: int = 0

    @classmethod
    def _filename(cls) -> str:
        return "test"

    @classmethod
    def _ext(cls) -> str:
        return ".test"


class ParsableModelWithMocks(ParsableModelBase):
    """ParsableFileModel test class using MagicMock for serializer and parser."""

    @classmethod
    def _get_serializer(cls):
        return MagicMock()

    @classmethod
    def _get_parser(cls):
        return MagicMock(return_value={"name": "parsed", "value": 42})


class ParsableModelWithDummies(ParsableModelBase):
    """ParsableFileModel test class using DummySerializer and DummyParser."""

    @classmethod
    def _get_serializer(cls):
        return DummySerializer.serialize

    @classmethod
    def _get_parser(cls):
        return DummmyParser.parse


class SaveModelBase(ParsableModelWithMocks):
    """Base class for testing save functionality."""

    @property
    def _resolved_filepath(self):
        return Path(f"{self.__class__.__name__.lower()}.test")

    def _load(self, filepath: Path) -> Dict:
        # Override _load to avoid file not found error
        return {"name": self.__class__.__name__.lower(), "value": 100}
