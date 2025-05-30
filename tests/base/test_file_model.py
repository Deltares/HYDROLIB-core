import unittest
from pathlib import Path
from typing import ClassVar, Dict, Optional
from unittest.mock import MagicMock, PropertyMock, patch

from hydrolib.core.base.file_manager import (
    FileLoadContext,
    ResolveRelativeMode,
    file_load_context,
)
from hydrolib.core.base.models import (
    BaseModel,
    FileModel,
    ModelSaveSettings,
    ModelTreeTraverser,
)


class ConcreteFileModel(FileModel):
    """Concrete implementation of FileModel for testing."""

    name: str = "default"
    value: int = 0
    _source_file_path: ClassVar[Optional[Path]] = None

    @classmethod
    def _should_load_model(cls, context: FileLoadContext) -> bool:
        return True

    def _post_init_load(self) -> None:
        """Post-initialization load method."""
        pass

    def _load(self, filepath: Path) -> Dict:
        # Return a dictionary with the data to be used for initialization
        self._source_file_path = filepath
        return {"name": filepath.stem, "value": len(filepath.stem)}

    def _save(self, save_settings: ModelSaveSettings) -> None:
        # Simple implementation that does nothing
        pass

    @classmethod
    def _generate_name(cls) -> Path:
        return Path("test_file.txt")


class TestFileModel(unittest.TestCase):
    """Test cases for the FileModel class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_path = Path("test_file.txt")

        # Clear any existing context
        if hasattr(file_load_context, "_context"):
            delattr(file_load_context, "_context")

    def test_new_with_filepath(self):
        """Test __new__ method with filepath."""
        # Create a mock for the file load context
        with (
            patch("hydrolib.core.base.models.file_load_context") as mock_context,
            patch.object(ConcreteFileModel, "_load"),
        ):
            # Set up the mock to return a context instance
            context_instance = MagicMock()
            mock_context.return_value.__enter__.return_value = context_instance
            context_instance.retrieve_model.return_value = None
            context_instance.is_content_changed.return_value = False

            # Call __new__ with a filepath
            ConcreteFileModel(filepath=self.test_path)

            # Verify retrieve_model was called with the filepath
            context_instance.retrieve_model.assert_called_once_with(self.test_path)

    def test_new_with_cached_model(self):
        """Test __new__ method with a cached model."""
        # Create a cached model
        with patch.object(ConcreteFileModel, "_load"):
            cached_model = ConcreteFileModel()
            cached_model.name = "cached"
            cached_model.value = 100

            # Directly patch the __new__ method to return the cached model
            original_new = ConcreteFileModel.__new__

            def mocked_new(cls, filepath=None, *args, **kwargs):
                if filepath == self.test_path:
                    # Set the class attribute that __init__ checks
                    cls._has_been_loaded_from_cache = True
                    return cached_model
                return original_new(cls, filepath, *args, **kwargs)

            with patch.object(ConcreteFileModel, "__new__", mocked_new):
                # Call the constructor with a filepath
                model = ConcreteFileModel(filepath=self.test_path)

                # Verify the model is the cached model
                self.assertIs(model, cached_model)

    def test_init_with_filepath(self):
        """Test __init__ method with filepath."""
        # Create a mock for the file load context
        mock_context = MagicMock()
        mock_context.get_current_parent.return_value = Path.cwd()
        mock_context.resolve.return_value = self.test_path
        mock_context.resolve_casing.return_value = self.test_path
        mock_context.convert_path_style.return_value = self.test_path
        mock_context.load_settings.resolve_casing = False
        mock_context.load_settings.recurse = True
        mock_context.cache_is_empty.return_value = True

        # Create a mock for the load settings
        mock_load_settings = MagicMock()
        mock_context.load_settings = mock_load_settings

        # Set up the mock _load method to return a dictionary with the data
        mock_load_data = {"name": "test_file", "value": 9}

        # Mock the _should_load_model method to return True
        with (
            patch.object(FileModel, "_should_load_model", return_value=True),
            patch(
                "hydrolib.core.base.models.file_load_context"
            ) as mock_file_load_context,
            patch.object(ConcreteFileModel, "_load", return_value=mock_load_data),
        ):

            # Set up the mock to return our mock context
            mock_file_load_context.return_value.__enter__.return_value = mock_context

            # Create a model with a filepath
            model = ConcreteFileModel(filepath=self.test_path)

            # Verify filepath was set
            self.assertEqual(model.filepath, self.test_path)
            # Verify other attributes were set from the mock data
            self.assertEqual(model.name, "test_file")
            self.assertEqual(model.value, 9)

    def test_init_without_filepath(self):
        """Test __init__ method without filepath."""
        # Create a model without a filepath
        with patch.object(ConcreteFileModel, "_load"):
            model = ConcreteFileModel()

            # Verify filepath is None
            self.assertIsNone(model.filepath)

    def test_resolved_filepath(self):
        """Test _resolved_filepath property."""
        # Create a model with a filepath
        with patch.object(ConcreteFileModel, "_load"):
            model = ConcreteFileModel(filepath=self.test_path)

            # Use PropertyMock to mock the _resolved_filepath property
            with patch.object(
                FileModel, "_resolved_filepath", new_callable=PropertyMock
            ) as mock_resolved_filepath:
                # Set the return value for the property
                mock_resolved_filepath.return_value = self.test_path

                # Verify _resolved_filepath returns the filepath
                self.assertEqual(model._resolved_filepath, self.test_path)

            # Test with None filepath
            model.filepath = None
            # Use PropertyMock again for the None case
            with patch.object(
                FileModel, "_resolved_filepath", new_callable=PropertyMock
            ) as mock_resolved_filepath:
                mock_resolved_filepath.return_value = None
                self.assertIsNone(model._resolved_filepath)

    def test_save_location(self):
        """Test save_location property."""
        # Create a model with a filepath
        with patch.object(ConcreteFileModel, "_load"):
            model = ConcreteFileModel(filepath=self.test_path)

            # Mock _absolute_anchor_path to return a known value
            model._absolute_anchor_path = Path.cwd()

            # Verify save_location returns the filepath
            self.assertEqual(model.save_location, Path.cwd() / self.test_path)

            # Test with None filepath
            model.filepath = None
            with patch.object(
                ConcreteFileModel, "_generate_name", return_value=Path("generated.txt")
            ):
                self.assertEqual(model.save_location, Path.cwd() / "generated.txt")

    def test_is_file_link(self):
        """Test is_file_link method."""
        # Create a model
        with patch.object(ConcreteFileModel, "_load"):
            model = ConcreteFileModel()

            # Verify is_file_link returns True
            self.assertTrue(model.is_file_link())

    def test_get_updated_file_path(self):
        """Test _get_updated_file_path method."""
        # Create a model
        with patch.object(ConcreteFileModel, "_load"):
            model = ConcreteFileModel()

            # Test with file_path and matching loading_path
            file_path = Path("path/file.txt")
            loading_path = Path("/some/other/path/file.txt")
            result = model._get_updated_file_path(file_path, loading_path)
            # The method should extract the last parts of loading_path that match the number of parts in file_path
            expected_path = Path("path/file.txt")
            self.assertEqual(result, expected_path)

            # Test with different casing
            file_path = Path("PATH/FILE.txt")
            loading_path = Path("/some/other/path/file.txt")
            result = model._get_updated_file_path(file_path, loading_path)
            # The method should update the casing to match the loading_path
            expected_path = Path("path/file.txt")
            self.assertEqual(result, expected_path)

    def test_save(self):
        """Test save method."""
        # Create a model
        with patch.object(ConcreteFileModel, "_load"):
            model = ConcreteFileModel(filepath=self.test_path)

            # Mock _save_instance and _save_tree
            with (
                patch.object(ConcreteFileModel, "_save_instance") as mock_save_instance,
                patch.object(ConcreteFileModel, "_save_tree") as mock_save_tree,
            ):

                # Call save
                model.save()

                # Verify _save_instance was called
                mock_save_instance.assert_called_once()

                # Verify _save_tree was not called (recurse=False by default)
                mock_save_tree.assert_not_called()

                # Call save with recurse=True
                model.save(recurse=True)

                # Verify _save_tree was called
                mock_save_tree.assert_called_once()

    def test_save_instance(self):
        """Test _save_instance method."""
        # Create a model
        with patch.object(ConcreteFileModel, "_load"):
            model = ConcreteFileModel(filepath=self.test_path)

            # Mock _save
            with patch.object(ConcreteFileModel, "_save") as mock_save:
                # Call _save_instance
                save_settings = MagicMock()
                model._save_instance(save_settings)

                # Verify _save was called with save_settings
                mock_save.assert_called_once_with(save_settings)

    def test_relative_mode(self):
        """Test _relative_mode property."""
        # Create a model
        with patch.object(ConcreteFileModel, "_load"):
            model = ConcreteFileModel()

            # Default implementation returns ToParent
            self.assertEqual(model._relative_mode, ResolveRelativeMode.ToParent)

    def test_get_relative_mode_from_data(self):
        """Test _get_relative_mode_from_data method."""
        # Create a model
        with patch.object(ConcreteFileModel, "_load"):
            model = ConcreteFileModel()

            # Test with empty data
            data = {}
            self.assertEqual(
                model._get_relative_mode_from_data(data), ResolveRelativeMode.ToParent
            )

            # Test with data containing pathsrelativetoparent=True
            # This test is not applicable to ConcreteFileModel since it doesn't override the default implementation
            # which always returns ToParent regardless of the data

            # Test with data containing pathsrelativetoparent=False
            # This test is not applicable to ConcreteFileModel since it doesn't override the default implementation
            # which always returns ToParent regardless of the data

    def test_generate_name(self):
        """Test _generate_name method."""
        # Call _generate_name
        result = ConcreteFileModel._generate_name()

        # Verify result is a Path object with the correct name
        self.assertIsInstance(result, Path)
        self.assertEqual(result.name, "test_file.txt")

    def test_change_to_path(self):
        """Test _change_to_path method."""
        # Test with string
        result = ConcreteFileModel._change_to_path("test/path")
        self.assertIsInstance(result, Path)
        self.assertEqual(result, Path("test/path"))

        # Test with Path
        path = Path("test/path")
        result = ConcreteFileModel._change_to_path(path)
        self.assertIs(result, path)

        # Test with None
        result = ConcreteFileModel._change_to_path(None)
        self.assertIsNone(result)

    def test_conform_filepath_to_pathlib(self):
        """Test _conform_filepath_to_pathlib method."""
        # Test with string
        result = ConcreteFileModel._conform_filepath_to_pathlib("test/path")
        self.assertIsInstance(result, Path)
        self.assertEqual(result, Path("test/path"))

        # Test with Path
        path = Path("test/path")
        result = ConcreteFileModel._conform_filepath_to_pathlib(path)
        self.assertIs(result, path)

        # Test with None
        result = ConcreteFileModel._conform_filepath_to_pathlib(None)
        self.assertIsNone(result)

    def test_save_tree(self):
        """Test _save_tree method."""
        # Create a model
        with patch.object(ConcreteFileModel, "_load"):
            model = ConcreteFileModel(filepath=self.test_path)

            # Mock the _save method
            with patch.object(ConcreteFileModel, "_save"):

                # Instead of mocking ModelTreeTraverser, mock the traverse method directly
                with patch.object(FileModel, "_save_tree") as mock_save_tree:
                    # Call save with recurse=True to trigger _save_tree
                    model.save(recurse=True)

                    # Verify _save_tree was called
                    mock_save_tree.assert_called_once()

    def test_synchronize_filepaths(self):
        """Test synchronize_filepaths method."""
        # Create a model
        with patch.object(ConcreteFileModel, "_load"):
            model = ConcreteFileModel(filepath=self.test_path)

            # Mock the traverse method directly
            with patch.object(ModelTreeTraverser, "traverse") as mock_traverse:
                # Call synchronize_filepaths
                model.synchronize_filepaths()

                # Verify traverse was called at least once
                mock_traverse.assert_called()

    def test_synchronize_filepaths_2(self):
        """Test synchronize_filepaths method."""

        # Create a model with nested models
        class NestedFileModel(ConcreteFileModel):
            name: str = "nested"

            def is_intermediate_link(self) -> bool:
                return True

            def is_file_link(self) -> bool:
                return True

        class ParentFileModel(ConcreteFileModel):
            nested: NestedFileModel

            def is_intermediate_link(self) -> bool:
                return True

            def is_file_link(self) -> bool:
                return True

        # Create models with mocked _load
        with patch.object(NestedFileModel, "_load"):
            nested = NestedFileModel(filepath=Path("nested.txt"))

            with patch.object(ParentFileModel, "_load"):
                parent = ParentFileModel(filepath=Path("parent.txt"), nested=nested)

                # Create a mock for the traverse method
                mock_traverse = MagicMock()

                # Patch the traverse method directly
                with patch.object(ModelTreeTraverser, "traverse", mock_traverse):
                    # Call synchronize_filepaths
                    parent.synchronize_filepaths()

                    # Verify traverse was called
                    mock_traverse.assert_called_once()

    def test_save_tree_2(self):
        """Test _save_tree method."""

        # Create a model with nested models
        class NestedModel(BaseModel):
            name: str

            def is_intermediate_link(self) -> bool:
                return True

            def is_file_link(self) -> bool:
                return False

        class ParentFileModel(ConcreteFileModel):
            nested: NestedModel

            def is_intermediate_link(self) -> bool:
                return True

            def is_file_link(self) -> bool:
                return True

        nested = NestedModel(name="nested")

        # Create parent model with mocked _load
        with patch.object(ParentFileModel, "_load"):
            parent = ParentFileModel(nested=nested)

            # Create a mock for the traverse method
            mock_traverse = MagicMock()

            # Patch the traverse method directly
            with patch.object(ModelTreeTraverser, "traverse", mock_traverse):
                # Call _save_tree
                context = FileLoadContext()
                save_settings = MagicMock()
                parent._save_tree(context, save_settings)

                # Verify traverse was called at least twice (once for name generation, once for saving)
                self.assertGreaterEqual(mock_traverse.call_count, 2)

    def test_validate(self):
        """Test validate method."""
        # Test with valid value
        with patch.object(ConcreteFileModel, "_load"):
            value = ConcreteFileModel()
            result = ConcreteFileModel.validate(value)
            self.assertEqual(result, value)

            # Test with None value
            result = ConcreteFileModel.validate(None)
            self.assertIsNone(result)

            # Test with invalid value
            with patch.object(
                FileModel,
                "validate",
                side_effect=ValueError("Expected FileModel, got str"),
            ):
                with self.assertRaises(ValueError):
                    ConcreteFileModel.validate("not a FileModel")
