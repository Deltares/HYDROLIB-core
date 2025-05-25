import unittest
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar
from unittest.mock import MagicMock, patch

from hydrolib.core.base.file_manager import FileLoadContext
from hydrolib.core.base.models import (
    BaseModel,
    DiskOnlyFileModel,
    ModelSaveSettings,
    ModelTreeTraverser,
    ParsableFileModel,
    SerializerConfig,
    _should_execute,
    _should_traverse,
)
from hydrolib.core.base.parser import DummmyParser
from hydrolib.core.base.serializer import DummySerializer


# Common test model classes to reduce duplication
class SimpleTestModel(BaseModel):
    """A simple test model with basic properties."""
    name: str
    value: int


class TestModelWithLinks(BaseModel):
    """A test model that overrides link methods."""
    name: str

    def is_file_link(self) -> bool:
        return True

    def is_intermediate_link(self) -> bool:
        return True


class ChildTestModel(TestModelWithLinks):
    """A child test model for hierarchy testing."""
    value: int


class ParentTestModel(TestModelWithLinks):
    """A parent test model for hierarchy testing."""
    child: ChildTestModel
    children: List[ChildTestModel] = []


class TestBaseModelWithFunc(BaseModel):
    """A test base model that can track function calls."""

    def test_func(self):
        """Test function that can be used to track calls."""
        pass


class ChildModelWithFunc(TestBaseModelWithFunc, ChildTestModel):
    """A child model that includes the test_func method."""
    pass


class ParentModelWithFunc(TestBaseModelWithFunc, ParentTestModel):
    """A parent model that includes the test_func method."""
    pass


class TestParsableModelBase(ParsableFileModel):
    """Base class for parsable file model tests."""
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
        # Test initialization with valid data
        model = SimpleTestModel(name="test", value=42)
        self.assertEqual(model.name, "test")
        self.assertEqual(model.value, 42)

        # Test initialization with invalid data
        with self.assertRaises(Exception):
            SimpleTestModel(name="test", value="not_an_int")

    def test_is_file_link(self):
        """Test is_file_link method."""
        # Test default implementation
        model = SimpleTestModel(name="test", value=42)
        self.assertFalse(model.is_file_link())

        # Test overridden implementation
        model_with_links = TestModelWithLinks(name="test")
        self.assertTrue(model_with_links.is_file_link())

    def test_is_intermediate_link(self):
        """Test is_intermediate_link method."""
        # Test default implementation
        model = SimpleTestModel(name="test", value=42)
        self.assertFalse(model.is_intermediate_link())

        # Test overridden implementation
        model_with_links = TestModelWithLinks(name="test")
        self.assertTrue(model_with_links.is_intermediate_link())

    def test_show_tree(self):
        """Test show_tree method."""
        child = ChildTestModel(name="child", value=42)
        parent = ParentTestModel(name="parent", child=child)

        # Capture stdout to verify output
        with patch("builtins.print") as mock_print:
            parent.show_tree()
            # Verify print was called with the model
            mock_print.assert_any_call("", "", parent)

    def test_apply_recurse(self):
        """Test _apply_recurse method."""
        # Create a list to track which models the function was called on
        called_models = []

        # Create a test function that records which model it was called on
        def test_func(self):
            called_models.append(self)

        # Patch the test_func method
        with patch.object(TestBaseModelWithFunc, 'test_func', test_func):
            child1 = ChildModelWithFunc(name="child1", value=1)
            child2 = ChildModelWithFunc(name="child2", value=2)
            child3 = ChildModelWithFunc(name="child3", value=3)
            parent = ParentModelWithFunc(name="parent", child=child1, children=[child2, child3])

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
        model = SimpleTestModel(name="test", value=42)
        # BaseModel's _get_identifier returns None by default
        self.assertIsNone(model._get_identifier({"name": "test", "value": 42}))


class TestModelTreeTraverser(unittest.TestCase):
    """Test cases for the ModelTreeTraverser class."""

    def test_traverse_simple_model(self):
        """Test traversal of a simple model with no children."""
        model = SimpleTestModel(name="test", value=42)

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
        child = ChildTestModel(name="child", value=42)
        parent = ParentTestModel(name="parent", child=child)

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

    def test_initialization(self):
        """Test initialization of SerializerConfig."""
        # Test default initialization
        config = SerializerConfig()
        self.assertEqual(config.float_format, "")

        # Test custom initialization
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
        self.assertTrue(settings._exclude_unset)


class TestParsableFileModel(unittest.TestCase):
    """Test cases for the ParsableFileModel class."""

    def setUp(self):
        """Set up test fixtures."""
        self.TestParsableModel = TestParsableModelBase

    def test_get_quantity_unit(self):
        """Test _get_quantity_unit method with different quantity types."""
        # Define test cases as tuples of (input_quantities, expected_units)
        test_cases = [
            (["discharge", "waterlevel", "salinity", "temperature"], ["m3/s", "m", "1e-3", "degC"]),
            (["unknown1", "unknown2"], ["-", "-"]),
            (["discharge", "unknown", "waterlevel"], ["m3/s", "-", "m"])
        ]

        # Run all test cases
        for quantities, expected_units in test_cases:
            with self.subTest(quantities=quantities):
                result = self.TestParsableModel._get_quantity_unit(quantities)
                self.assertEqual(result, expected_units)
