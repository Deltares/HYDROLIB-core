from typing import List

from hydrolib.core.base.models import BaseModel


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
