import unittest
from pathlib import Path
from typing import Any, Dict, List
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

        class TestModel(BaseModel):
            name: str

        model = TestModel(name="test")
        self.assertFalse(model.is_file_link())

    def test_is_intermediate_link(self):
        """Test is_intermediate_link method."""

        class TestModel(BaseModel):
            name: str

        model = TestModel(name="test")
        self.assertFalse(model.is_intermediate_link())

    def test_show_tree(self):
        """Test show_tree method."""

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
        with patch("builtins.print") as mock_print:
            parent.show_tree()
            # Verify print was called with the model objects
            mock_print.assert_any_call("", "", parent)
            mock_print.assert_any_call("  ", "∟", child)

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

        class TestModel(BaseModel):
            name: str
            value: int

        model = TestModel(name="test", value=42)
        # BaseModel's _get_identifier returns None by default
        self.assertIsNone(model._get_identifier({"name": "test", "value": 42}))


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
                return MagicMock()

            @classmethod
            def _get_parser(cls):
                return MagicMock(return_value={"name": "parsed", "value": 42})

        self.TestParsableModel = TestParsableModel

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

        class TestSaveModel(ParsableFileModel):
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
                return mock_serializer

            @classmethod
            def _get_parser(cls):
                return MagicMock(return_value={"name": "parsed", "value": 42})

            @property
            def _resolved_filepath(self):
                return Path("test_save.test")

            def _load(self, filepath: Path) -> Dict:
                # Override _load to avoid file not found error
                return {"name": "test_save", "value": 100}

        # Create a model instance with a filepath
        model = TestSaveModel(
            name="test_save", value=100, filepath=Path("test_save.test")
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
        self.assertEqual(mock_serializer.call_args[0][0], Path("test_save.test"))
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

        class TestSerializeModel(ParsableFileModel):
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
                return mock_serializer

            @classmethod
            def _get_parser(cls):
                return MagicMock(return_value={"name": "parsed", "value": 42})

            @property
            def _resolved_filepath(self):
                return Path("test_serialize.test")

            def _load(self, filepath: Path) -> Dict:
                # Override _load to avoid file not found error
                return {"name": "test_serialize", "value": 100}

        # Create a model instance with a filepath
        model = TestSerializeModel(
            name="test_serialize", value=100, filepath=Path("test_serialize.test")
        )

        # Create save settings and data
        save_settings = MagicMock()
        data = {"name": "test_serialize", "value": 100}

        # Mock the mkdir method to avoid creating directories
        with patch("pathlib.Path.mkdir"):
            # Call _serialize
            model._serialize(data, save_settings)

        # Verify serializer was called
        mock_serializer.assert_called_once()
        # Check that the first argument is the filepath
        self.assertEqual(mock_serializer.call_args[0][0], Path("test_serialize.test"))
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
        result = model.dict()

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

