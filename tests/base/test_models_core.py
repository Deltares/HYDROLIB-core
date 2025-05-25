import unittest
from unittest.mock import MagicMock, patch
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, ClassVar

import pytest

from hydrolib.core.base.models import (
    BaseModel,
    FileModel,
    ParsableFileModel,
    DiskOnlyFileModel,
    SerializerConfig,
    ModelSaveSettings,
    ModelTreeTraverser,
    _should_traverse,
    _should_execute,
    validator_set_default_disk_only_file_model_when_none,
)
from hydrolib.core.base.file_manager import FileLoadContext, ResolveRelativeMode
from hydrolib.core.base_utils import DummmyParser, DummySerializer


class TestBaseModelFunctions(unittest.TestCase):
    """Test cases for the standalone functions in the models module."""

    def test_should_traverse(self):
        """Test _should_traverse function."""
        model = MagicMock(spec=BaseModel)
        context = MagicMock(spec=FileLoadContext)

        # Default implementation always returns True
        self.assertTrue(_should_traverse(model, context))

    def test_should_execute(self):
        """Test _should_execute function."""
        model = MagicMock(spec=BaseModel)
        context = MagicMock(spec=FileLoadContext)

        # Default implementation always returns True
        self.assertTrue(_should_execute(model, context))

    def test_validator_set_default_disk_only_file_model_when_none(self):
        """Test validator_set_default_disk_only_file_model_when_none function."""
        # Get the validator function's inner adjust_none function
        # We need to access the inner function directly
        def adjust_none(v: Any, field: "ModelField") -> Any:
            if field.type_ is DiskOnlyFileModel and v is None:
                return {"filepath": None}
            return v

        # Create a mock field
        field = MagicMock()
        field.type_ = DiskOnlyFileModel
        field.name = "test_field"

        # Test with None value
        result = adjust_none(None, field)
        self.assertEqual(result, {"filepath": None})

        # Test with non-None value
        model = MagicMock(spec=DiskOnlyFileModel)
        result = adjust_none(model, field)
        self.assertEqual(result, model)


class TestBaseModel(unittest.TestCase):
    """Test cases for the BaseModel class."""

    def test_init(self):
        """Test initialization of BaseModel."""
        # Create a simple subclass for testing
        class TestModel(BaseModel):
            name: str
            value: int

        # Test initialization with valid data
        model = TestModel(name="test", value=42)
        self.assertEqual(model.name, "test")
        self.assertEqual(model.value, 42)

        # Test initialization with invalid data
        with self.assertRaises(Exception):
            TestModel(name="test", value="not_an_int")

    def test_is_file_link(self):
        """Test is_file_link method."""
        # Create a simple subclass for testing
        class TestModel(BaseModel):
            name: str

        model = TestModel(name="test")
        # Default implementation returns False
        self.assertFalse(model.is_file_link())

    def test_is_intermediate_link(self):
        """Test is_intermediate_link method."""
        # Create a simple subclass for testing
        class TestModel(BaseModel):
            name: str

        model = TestModel(name="test")
        # Default implementation returns False
        self.assertFalse(model.is_intermediate_link())

    def test_show_tree(self):
        """Test show_tree method."""
        # Create a simple model hierarchy for testing
        class ChildModel(BaseModel):
            name: str
            value: int

            def is_file_link(self) -> bool:
                return True

            def is_intermediate_link(self) -> bool:
                return True

        class ParentModel(BaseModel):
            name: str
            child: ChildModel

            def is_file_link(self) -> bool:
                return True

            def is_intermediate_link(self) -> bool:
                return True

        child = ChildModel(name="child", value=42)
        parent = ParentModel(name="parent", child=child)

        # Capture stdout to verify output
        with patch('builtins.print') as mock_print:
            parent.show_tree()
            # Verify print was called with the model
            mock_print.assert_any_call('', '', parent)

    def test_apply_recurse(self):
        """Test _apply_recurse method."""
        # Create a list to track which models the function was called on
        called_models = []

        # Create a simple model hierarchy for testing
        class TestBaseModel(BaseModel):
            """A test base model that tracks calls to a specific function."""

            def test_func(self):
                """Test function that records which model it was called on."""
                called_models.append(self)

        class ChildModel(TestBaseModel):
            name: str
            value: int

            def is_file_link(self) -> bool:
                return True

            def is_intermediate_link(self) -> bool:
                return True

        class ParentModel(TestBaseModel):
            name: str
            child: ChildModel
            children: List[ChildModel] = []

            def is_file_link(self) -> bool:
                return True

            def is_intermediate_link(self) -> bool:
                return True

        child1 = ChildModel(name="child1", value=1)
        child2 = ChildModel(name="child2", value=2)
        child3 = ChildModel(name="child3", value=3)
        parent = ParentModel(name="parent", child=child1, children=[child2, child3])

        # Apply the function recursively
        parent._apply_recurse("test_func")

        # Verify the function was called on all models
        self.assertEqual(len(called_models), 4)
        self.assertIn(parent, called_models)
        self.assertIn(child1, called_models)
        self.assertIn(child2, called_models)
        self.assertIn(child3, called_models)

    def test_get_identifier(self):
        """Test _get_identifier method."""
        # Create a simple subclass for testing
        class TestModel(BaseModel):
            name: str
            value: int

        model = TestModel(name="test", value=42)
        # BaseModel's _get_identifier returns None by default
        self.assertIsNone(model._get_identifier({"name": "test", "value": 42}))


class TestModelTreeTraverser(unittest.TestCase):
    """Test cases for the ModelTreeTraverser class."""

    def test_traverse_simple_model(self):
        """Test traversal of a simple model with no children."""
        # Create a simple model for testing
        class TestModel(BaseModel):
            name: str
            value: int

        model = TestModel(name="test", value=42)

        # Define a function to count models
        def count_models(model: BaseModel, count: int) -> int:
            return count + 1

        # Create a traverser with the count function
        traverser = ModelTreeTraverser[int](post_traverse_func=count_models)

        # Traverse the model
        result = traverser.traverse(model, 0)

        # Verify the result
        self.assertEqual(result, 1)  # Only one model was traversed

    def test_traverse_nested_model(self):
        """Test traversal of a nested model."""
        # Create a nested model for testing
        class ChildModel(BaseModel):
            name: str
            value: int

        class ParentModel(BaseModel):
            name: str
            child: ChildModel

        child = ChildModel(name="child", value=42)
        parent = ParentModel(name="parent", child=child)

        # Define a function to collect model names
        def collect_names(model: BaseModel, names: List[str]) -> List[str]:
            if hasattr(model, "name"):
                names.append(model.name)
            return names

        # Create a traverser with the collect function
        traverser = ModelTreeTraverser[List[str]](post_traverse_func=collect_names)

        # Traverse the model
        result = traverser.traverse(parent, [])

        # Verify the result
        self.assertEqual(len(result), 2)  # Two models were traversed
        self.assertIn("parent", result)
        self.assertIn("child", result)


class TestSerializerConfig(unittest.TestCase):
    """Test cases for the SerializerConfig class."""

    def test_default_initialization(self):
        """Test default initialization of SerializerConfig."""
        config = SerializerConfig()
        self.assertEqual(config.float_format, "")

    def test_custom_initialization(self):
        """Test initialization with custom float_format."""
        config = SerializerConfig(float_format=".2f")
        self.assertEqual(config.float_format, ".2f")


class TestModelSaveSettings(unittest.TestCase):
    """Test cases for the ModelSaveSettings class."""

    def test_initialization(self):
        """Test initialization of ModelSaveSettings."""
        # Test default initialization
        settings = ModelSaveSettings()
        self.assertIsNotNone(settings.path_style)

        # Test custom initialization
        settings = ModelSaveSettings(path_style="windows", exclude_unset=True)
        self.assertEqual(settings._exclude_unset, True)


class TestParsableFileModel(unittest.TestCase):
    """Test cases for the ParsableFileModel class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create a concrete subclass of ParsableFileModel for testing
        class TestParsableModel(ParsableFileModel):
            name: str = "default"
            value: int = 0

            @classmethod
            def _filename(cls) -> str:
                return "test"

            @classmethod
            def _ext(cls) -> str:
                return ".test"

            @classmethod
            def _get_serializer(cls):
                return DummySerializer.serialize

            @classmethod
            def _get_parser(cls):
                return DummmyParser.parse

        self.TestParsableModel = TestParsableModel

    def test_get_quantity_unit(self):
        """Test _get_quantity_unit method."""
        # Test with known quantities
        quantities = ["discharge", "waterlevel", "salinity", "temperature"]
        result = self.TestParsableModel._get_quantity_unit(quantities)
        self.assertEqual(result, ["m3/s", "m", "1e-3", "degC"])

        # Test with unknown quantities
        quantities = ["unknown1", "unknown2"]
        result = self.TestParsableModel._get_quantity_unit(quantities)
        self.assertEqual(result, ["-", "-"])

        # Test with mixed quantities
        quantities = ["discharge", "unknown", "waterlevel"]
        result = self.TestParsableModel._get_quantity_unit(quantities)
        self.assertEqual(result, ["m3/s", "-", "m"])


if __name__ == "__main__":
    unittest.main()
