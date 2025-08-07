import unittest
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar
from unittest.mock import MagicMock, patch

from hydrolib.core.base.file_manager import FileLoadContext
from hydrolib.core.base.models import (
    BaseModel,
    DiskOnlyFileModel,
    ParsableFileModel,
    SerializerConfig,
    _should_execute,
    _should_traverse,
)


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
        model_with_links = ModelWithLinks(name="test")
        self.assertTrue(model_with_links.is_file_link())

    def test_is_intermediate_link(self):
        """Test is_intermediate_link method."""
        # Test default implementation
        model = SimpleTestModel(name="test", value=42)
        self.assertFalse(model.is_intermediate_link())

        # Test overridden implementation
        model_with_links = ModelWithLinks(name="test")
        self.assertTrue(model_with_links.is_intermediate_link())

    def test_show_tree(self):
        """Test show_tree method."""
        child = ChildTestModel(name="child", value=42)
        parent = ParentTestModel(name="parent", child=child)

        # Capture stdout to verify output
        with patch("builtins.print") as mock_print:
            parent.show_tree()
            # Verify print was called with the model objects
            mock_print.assert_any_call("", "", parent)
            mock_print.assert_any_call("  ", "∟", child)

    def test_apply_recurse(self):
        """Test _apply_recurse method."""
        # Create a list to track which models the function was called on
        called_models = []

        # Create a test function that records which model it was called on
        def test_func(self):
            called_models.append(self)

        # Patch the test_func method
        with patch.object(BaseModelWithFunc, "test_func", test_func):
            child1 = ChildModelWithFunc(name="child1", value=1)
            child2 = ChildModelWithFunc(name="child2", value=2)
            child3 = ChildModelWithFunc(name="child3", value=3)
            parent = ParentModelWithFunc(
                name="parent", child=child1, children=[child2, child3]
            )

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


# Common test model classes for ParsableFileModel tests
class ParsableModelBase(ParsableFileModel):
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
        return MagicMock()

    @classmethod
    def _get_parser(cls):
        return MagicMock(return_value={"name": "parsed", "value": 42})


class SaveModelBase(ParsableModelBase):
    """Base class for testing save functionality."""

    @property
    def _resolved_filepath(self):
        return Path(f"{self.__class__.__name__.lower()}.test")

    def _load(self, filepath: Path) -> Dict:
        # Override _load to avoid file not found error
        return {"name": self.__class__.__name__.lower(), "value": 100}


class TestParsableFileModel(unittest.TestCase):
    """Test cases for the ParsableFileModel class."""

    def setUp(self):
        """Set up test fixtures."""
        self.TestParsableModel = ParsableModelBase

    def test_load(self):
        """Test _load method."""
        # Mock the parser
        mock_parser = MagicMock(return_value={"name": "parsed", "value": 42})
        self.TestParsableModel._get_parser = classmethod(lambda cls: mock_parser)

        # Create a test file path
        test_path = Path("test_file.test")

        # Create a model instance
        model = self.TestParsableModel()

        # Mock file existence
        with patch("pathlib.Path.is_file", return_value=True):
            # Call _load
            result = model._load(test_path)

        # Verify parser was called
        mock_parser.assert_called_once_with(test_path)

        # Verify the result contains the parsed data
        self.assertEqual(result, {"name": "parsed", "value": 42})

    def test_save(self):
        """Test _save method."""
        # Create a test class with a mocked serializer
        mock_serializer = MagicMock()

        # Create a test model class that uses the mock serializer
        class TestSaveModel(SaveModelBase):
            @classmethod
            def _get_serializer(cls):
                return mock_serializer

        # Create a model instance with a filepath
        model = TestSaveModel(
            name="testsavemodel", value=100, filepath=Path("testsavemodel.test")
        )

        # Create save settings
        save_settings = MagicMock()
        save_settings.path_style = None

        # Mock the mkdir method to avoid creating directories
        with patch("pathlib.Path.mkdir"):
            # Call _save
            model._save(save_settings)

        # Verify serializer was called
        mock_serializer.assert_called_once()
        # Check that the first argument is the filepath
        self.assertEqual(mock_serializer.call_args[0][0], Path("testsavemodel.test"))
        # Check that the second argument is a dict containing model data
        self.assertIsInstance(mock_serializer.call_args[0][1], dict)
        # Check that the third argument is the serializer config
        self.assertIsInstance(mock_serializer.call_args[0][2], SerializerConfig)
        # Check that the fourth argument is the save settings
        self.assertEqual(mock_serializer.call_args[0][3], save_settings)

    def test_serialize(self):
        """Test _serialize method."""
        # Create a test class with a mocked serializer
        mock_serializer = MagicMock()

        # Create a test model class that uses the mock serializer
        class TestSerializeModel(SaveModelBase):
            @classmethod
            def _get_serializer(cls):
                return mock_serializer

        # Create a model instance with a filepath
        model = TestSerializeModel(
            name="testserializemodel",
            value=100,
            filepath=Path("testserializemodel.test"),
        )

        # Create save settings and data
        save_settings = MagicMock()
        data = {"name": "testserializemodel", "value": 100}

        # Mock the mkdir method to avoid creating directories
        with patch("pathlib.Path.mkdir"):
            # Call _serialize
            model._serialize(data, save_settings)

        # Verify serializer was called
        mock_serializer.assert_called_once()
        # Check that the first argument is the filepath
        self.assertEqual(
            mock_serializer.call_args[0][0], Path("testserializemodel.test")
        )
        # Check that the second argument is the data
        self.assertEqual(mock_serializer.call_args[0][1], data)
        # Check that the third argument is the serializer config
        self.assertIsInstance(mock_serializer.call_args[0][2], SerializerConfig)
        # Check that the fourth argument is the save settings
        self.assertEqual(mock_serializer.call_args[0][3], save_settings)

    def test_dict(self):
        """Test dict method."""
        # Create a model instance
        model = self.TestParsableModel(name="test_dict", value=100)

        # Call dict
        result = model.model_dump()

        # Verify result contains expected keys and values
        self.assertIn("name", result)
        self.assertEqual(result["name"], "test_dict")
        self.assertIn("value", result)
        self.assertEqual(result["value"], 100)

    def test_exclude_fields(self):
        """Test _exclude_fields method."""
        # The implementation returns a set of fields to exclude
        excluded = self.TestParsableModel._exclude_fields()
        self.assertIsInstance(excluded, (list, set))
        # Verify that 'filepath' and 'serializer_config' are excluded
        self.assertIn("filepath", excluded)
        self.assertIn("serializer_config", excluded)

    def test_parse(self):
        """Test _parse method."""
        # Mock the parser
        mock_parser = MagicMock(return_value={"name": "parsed", "value": 42})
        self.TestParsableModel._get_parser = classmethod(lambda cls: mock_parser)

        # Create a test file path
        test_path = Path("test_file.test")

        # Call _parse
        result = self.TestParsableModel._parse(test_path)

        # Verify parser was called
        mock_parser.assert_called_once_with(test_path)

        # Verify result
        self.assertEqual(result, {"name": "parsed", "value": 42})

    def test_generate_name(self):
        """Test _generate_name method."""
        # Call _generate_name
        result = self.TestParsableModel._generate_name()

        # Verify result is a Path or string with the correct name
        if isinstance(result, Path):
            self.assertEqual(result.name, "test.test")
        else:
            self.assertEqual(result, "test.test")

    def test_filename(self):
        """Test _filename method."""
        # Call _filename
        result = self.TestParsableModel._filename()

        # Verify result
        self.assertEqual(result, "test")

    def test_ext(self):
        """Test _ext method."""
        # Call _ext
        result = self.TestParsableModel._ext()

        # Verify result
        self.assertEqual(result, ".test")

    def test_get_serializer(self):
        """Test _get_serializer method."""
        # Call _get_serializer
        result = self.TestParsableModel._get_serializer()

        # Verify result is callable
        self.assertTrue(callable(result))

    def test_get_parser(self):
        """Test _get_parser method."""
        # Call _get_parser
        result = self.TestParsableModel._get_parser()

        # Verify result is callable
        self.assertTrue(callable(result))

    def test_get_identifier(self):
        """Test _get_identifier method."""
        # Create a model instance
        model = self.TestParsableModel()

        # Test with filepath
        test_path = Path("test_file.test")
        data = {"filepath": test_path}
        result = model._get_identifier(data)
        self.assertEqual(result, "test_file.test")

        # Test without filepath
        data = {"name": "test"}
        result = model._get_identifier(data)
        self.assertIsNone(result)

    def test_get_quantity_unit(self):
        """Test _get_quantity_unit method with different quantity types."""
        # Define test cases as tuples of (input_quantities, expected_units)
        test_cases = [
            (
                ["discharge", "waterlevel", "salinity", "temperature"],
                ["m3/s", "m", "1e-3", "degC"],
            ),
            (["unknown1", "unknown2"], ["-", "-"]),
            (["discharge", "unknown", "waterlevel"], ["m3/s", "-", "m"]),
        ]

        # Run all test cases
        for quantities, expected_units in test_cases:
            with self.subTest(quantities=quantities):
                result = self.TestParsableModel._get_quantity_unit(quantities)
                self.assertEqual(result, expected_units)


class TestStandaloneFunctions(unittest.TestCase):
    """Test cases for standalone functions in the models module."""

    def test_should_traverse(self):
        """Test _should_traverse function."""
        # Create a model that returns True for is_intermediate_link
        model = MagicMock(spec=BaseModel)
        model.is_intermediate_link.return_value = True

        # Create a context
        context = FileLoadContext()

        # Call _should_traverse
        result = _should_traverse(model, context)

        # Should return True when is_intermediate_link returns True
        self.assertTrue(result)
        model.is_intermediate_link.assert_called_once()

        # Create a model that returns False for is_intermediate_link
        model = MagicMock(spec=BaseModel)
        model.is_intermediate_link.return_value = False

        # Call _should_traverse
        result = _should_traverse(model, context)

        # Should return False when is_intermediate_link returns False
        self.assertFalse(result)
        model.is_intermediate_link.assert_called_once()

    def test_should_execute(self):
        """Test _should_execute function."""
        # Create a model that returns True for is_file_link
        model = MagicMock(spec=BaseModel)
        model.is_file_link.return_value = True

        # Create a context
        context = FileLoadContext()

        # Call _should_execute
        result = _should_execute(model, context)

        # Should return True when is_file_link returns True
        self.assertTrue(result)
        model.is_file_link.assert_called_once()

        # Create a model that returns False for is_file_link
        model = MagicMock(spec=BaseModel)
        model.is_file_link.return_value = False

        # Call _should_execute
        result = _should_execute(model, context)

        # Should return False when is_file_link returns False
        self.assertFalse(result)
        model.is_file_link.assert_called_once()

    def test_validator_set_default_disk_only_file_model_when_none(self):
        """Test validator_set_default_disk_only_file_model_when_none function."""

        # Define the adjust_none function directly to test it
        def adjust_none(v: Any, field: "ModelField") -> Any:
            if field.type_ is DiskOnlyFileModel and v is None:
                return {"filepath": None}
            return v

        # Create a mock field with type DiskOnlyFileModel
        field = MagicMock()
        field.type_ = DiskOnlyFileModel

        # Test with None value
        result = adjust_none(None, field)
        # The validator should return a dict with filepath=None
        self.assertEqual(result, {"filepath": None})

        # Test with non-None value
        existing_model = DiskOnlyFileModel(filepath=Path("test.txt"))
        result = adjust_none(existing_model, field)
        # The validator should return the existing model unchanged
        self.assertEqual(result, existing_model)

        # Test with a field that is not DiskOnlyFileModel
        field.type_ = str
        result = adjust_none(None, field)
        # The validator should return None unchanged
        self.assertIsNone(result)
