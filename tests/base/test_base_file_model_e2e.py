"""
End-to-end tests for the FileModel class.

These tests use actual files on disk to test the behaviors of the FileModel class.
"""

import shutil
import tempfile
import unittest
from pathlib import Path
from typing import Dict, Optional

from hydrolib.core.base.file_manager import ResolveRelativeMode, file_load_context
from hydrolib.core.base.models import FileModel, ModelSaveSettings


class SimpleFileModel(FileModel):
    """A concrete implementation of FileModel for testing.

    This model reads and writes simple text files with key=value pairs.
    """

    name: str = "default"
    value: int = 0
    description: Optional[str] = None
    child_file: Optional["SimpleFileModel"] = None
    child_file1: Optional["SimpleFileModel"] = None
    child_file2: Optional["SimpleFileModel"] = None
    child_file3: Optional["SimpleFileModel"] = None

    def _post_init_load(self) -> None:
        """Post-initialization load method."""
        pass

    def _load(self, filepath: Path) -> Dict:
        """Load data from a simple text file with key=value pairs.

        Args:
            filepath: Path to the file to load.

        Returns:
            Dict: Dictionary with the data loaded from the file.

        Raises:
            FileNotFoundError: If the file does not exist.
        """
        if not filepath.exists():
            raise FileNotFoundError(f"File {filepath} not found")

        data = {}
        with open(filepath, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                key, value = line.split("=", 1)

                # Handle special cases for different types
                if key == "value":
                    data[key] = int(value)
                elif key in ["child_file", "child_file1", "child_file2", "child_file3"]:
                    # For child files, store the path
                    data[key] = Path(value)
                else:
                    data[key] = value

        return data

    def _save(self, save_settings: ModelSaveSettings) -> None:
        """Save the model to a simple text file with key=value pairs.

        Args:
            save_settings: Settings for saving the model.
        """
        filepath = self._resolved_filepath
        if filepath is None:
            return

        # Create parent directory if it doesn't exist
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # Write the file
        with open(filepath, "w") as f:
            for key, value in self.__dict__.items():
                # Skip private attributes and filepath
                if key.startswith("_") or key == "filepath":
                    continue

                # Skip None values
                if value is None:
                    continue

                # Handle child file references
                if key in [
                    "child_file",
                    "child_file1",
                    "child_file2",
                    "child_file3",
                ] and isinstance(value, FileModel):
                    # Get the relative path from this file to the child file
                    if value.filepath is not None:
                        child_path = value.filepath
                        f.write(f"{key}={child_path}\n")
                else:
                    f.write(f"{key}={value}\n")

    @classmethod
    def _generate_name(cls) -> Path:
        """Generate a default name for this model.

        Returns:
            Path: A path with the default name.
        """
        return Path("simple_file.txt")


class TestFileModelE2E(unittest.TestCase):
    """End-to-end tests for the FileModel class."""

    def setUp(self):
        """Set up test fixtures.

        Creates a temporary directory for test output and copies test input files.
        """
        # Create a temporary directory for test output
        # self.temp_dir = Path("tests/data/output/delete_me").absolute()
        self.temp_dir = Path(tempfile.mkdtemp())
        # Ensure the directory exists and is empty
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        print(
            f"Temporary directory: {self.temp_dir} (absolute: {self.temp_dir.is_absolute()})"
        )

        # Path to the test input files
        self.input_dir = Path("tests/data/input/base_file_model_tests").absolute()
        print(
            f"Input directory: {self.input_dir} (absolute: {self.input_dir.is_absolute()})"
        )

        # Copy test input files to the temporary directory
        for file in self.input_dir.glob("**/*"):
            if file.is_file():
                # Create the parent directory in the temp dir
                rel_path = file.relative_to(self.input_dir)
                dest_path = self.temp_dir / rel_path
                dest_path.parent.mkdir(parents=True, exist_ok=True)

                # Copy the file
                shutil.copy2(file, dest_path)

        # Clear any existing context
        if hasattr(file_load_context, "_context"):
            delattr(file_load_context, "_context")

    def tearDown(self):
        """Tear down test fixtures.

        Clears the contents of the temporary directory.
        """
        # Clear the contents of the temporary directory
        for item in self.temp_dir.glob("*"):
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

    def test_load_simple_file(self):
        """Test loading a simple file.

        This test verifies that a FileModel can load data from a simple file.
        The expected behavior is that the model's attributes are set from the file's contents.
        """
        # Path to the test file
        file_path = self.temp_dir / "simple_file.txt"

        # Load the file
        model = SimpleFileModel(filepath=file_path)

        # Verify the model's attributes
        self.assertEqual(model.name, "simple_file")
        self.assertEqual(model.value, 10)
        self.assertEqual(model.description, "This is a simple test file")
        self.assertEqual(model.filepath, file_path)

    def test_save_simple_file(self):
        """Test saving a simple file.

        This test verifies that a FileModel can save data to a simple file.
        The expected behavior is that the file's contents match the model's attributes.
        """
        model = SimpleFileModel(
            name="test_save", value=42, description="Test save operation"
        )

        save_path = self.temp_dir / "saved_file.txt"
        model.save(filepath=save_path)

        # Verify the file was created
        self.assertTrue(save_path.exists())

        # Load the file again to verify its contents
        loaded_model = SimpleFileModel(filepath=save_path)

        # Verify the loaded model's attributes
        self.assertEqual(loaded_model.name, "test_save")
        self.assertEqual(loaded_model.value, 42)
        self.assertEqual(loaded_model.description, "Test save operation")

    def test_recursive_load(self):
        """Test recursive loading of files.

        This test verifies that a FileModel can recursively load child models.
        The expected behavior is that the parent model and all child models are loaded correctly.
        """
        # Path to the parent file
        parent_path = self.temp_dir / "parent_file.txt"

        # Load the parent file with recurse=True (default)
        parent_model = SimpleFileModel(filepath=parent_path)

        # Verify the parent model's attributes
        self.assertEqual(parent_model.name, "parent_file")
        self.assertEqual(parent_model.value, 5)

        # Verify the child model was loaded
        self.assertIsNotNone(parent_model.child_file)
        self.assertEqual(parent_model.child_file.name, "simple_file")
        self.assertEqual(parent_model.child_file.value, 10)
        self.assertEqual(
            parent_model.child_file.description, "This is a simple test file"
        )

    def test_recursive_save(self):
        """Test recursive saving of files.

        This test verifies that a FileModel can recursively save child models.
        The expected behavior:
            the parent model and all child models are saved correctly.

        Note:
            When using recursive save, the child models must be properly linked to the parent model through one of
            its fields (like child_file in this case). The child model's filepath should be set before assigning it
            to the parent, or the parent's filepath should be set before the recursive save operation.
        """
        # Create a parent model with a child
        child_model = SimpleFileModel(
            name="child_save", value=100, description="Child model"
        )

        # Set the child model's filepath before assigning it to the parent
        child_save_path = self.temp_dir / "child_save.txt"
        child_model.filepath = child_save_path
        print(
            f"Child model filepath: {child_model.filepath} (absolute: {child_model.filepath.is_absolute()})"
        )
        print(
            f"Child model save_location: {child_model.save_location} (absolute: {child_model.save_location.is_absolute()})"
        )
        print(
            f"Child model _absolute_anchor_path: {child_model._absolute_anchor_path} (absolute: {child_model._absolute_anchor_path.is_absolute()})"
        )

        # Create the parent model with the child model
        parent_model = SimpleFileModel(
            name="parent_save", value=200, child_file=child_model
        )

        # Set the parent model's filepath
        parent_save_path = self.temp_dir / "parent_save.txt"
        parent_model.filepath = parent_save_path
        print(
            f"Parent model filepath: {parent_model.filepath} (absolute: {parent_model.filepath.is_absolute()})"
        )
        print(
            f"Parent model save_location: {parent_model.save_location} (absolute: {parent_model.save_location.is_absolute()})"
        )
        print(
            f"Parent model _absolute_anchor_path: {parent_model._absolute_anchor_path} (absolute: {parent_model._absolute_anchor_path.is_absolute()})"
        )

        # Save the parent model recursively
        parent_model.save(recurse=True)
        print(
            f"After save - Child model filepath: {child_model.filepath} (absolute: {child_model.filepath.is_absolute()})"
        )
        print(
            f"After save - Child model save_location: {child_model.save_location} (absolute: {child_model.save_location.is_absolute()})"
        )
        print(
            f"After save - Child model _absolute_anchor_path: {child_model._absolute_anchor_path} (absolute: {child_model._absolute_anchor_path.is_absolute()})"
        )
        print(
            f"After save - Parent model filepath: {parent_model.filepath} (absolute: {parent_model.filepath.is_absolute()})"
        )
        print(
            f"After save - Parent model save_location: {parent_model.save_location} (absolute: {parent_model.save_location.is_absolute()})"
        )
        print(
            f"After save - Parent model _absolute_anchor_path: {parent_model._absolute_anchor_path} (absolute: {parent_model._absolute_anchor_path.is_absolute()})"
        )

        # Verify both files were created
        self.assertTrue(parent_save_path.exists())
        self.assertTrue(child_save_path.exists())

        # Load the files again to verify their contents
        loaded_parent = SimpleFileModel(filepath=parent_save_path)

        # Verify the loaded models' attributes
        self.assertEqual(loaded_parent.name, "parent_save")
        self.assertEqual(loaded_parent.value, 200)
        self.assertEqual(loaded_parent.child_file.name, "child_save")
        self.assertEqual(loaded_parent.child_file.value, 100)
        self.assertEqual(loaded_parent.child_file.description, "Child model")

    def test_recursive_save_unrelated_child(self):
        """Test recursive saving with an unrelated child model.

        This test demonstrates what happens when a child model is not properly linked to the parent model.
        The expected behavior is that the child model is not saved when the parent model is saved recursively,
        because the child model is not recognized as a child of the parent model during the recursive save operation.

        This is different from the test_recursive_save test, where the child model is properly linked to the parent model
        through the child_file field, and both models are saved when the parent model is saved recursively.
        """
        # Create a parent model and a separate, unrelated child model
        parent_model = SimpleFileModel(name="parent_save", value=200)
        child_model = SimpleFileModel(
            name="child_save", value=100, description="Child model"
        )

        # Set the filepaths for both models
        parent_save_path = self.temp_dir / "parent_save_unrelated.txt"
        child_save_path = self.temp_dir / "child_save_unrelated.txt"
        parent_model.filepath = parent_save_path
        child_model.filepath = child_save_path
        print(
            f"Unrelated - Child model filepath: {child_model.filepath} (absolute: {child_model.filepath.is_absolute()})"
        )
        print(
            f"Unrelated - Child model save_location: {child_model.save_location} (absolute: {child_model.save_location.is_absolute()})"
        )
        print(
            f"Unrelated - Child model _absolute_anchor_path: {child_model._absolute_anchor_path} (absolute: {child_model._absolute_anchor_path.is_absolute()})"
        )
        print(
            f"Unrelated - Parent model filepath: {parent_model.filepath} (absolute: {parent_model.filepath.is_absolute()})"
        )
        print(
            f"Unrelated - Parent model save_location: {parent_model.save_location} (absolute: {parent_model.save_location.is_absolute()})"
        )
        print(
            f"Unrelated - Parent model _absolute_anchor_path: {parent_model._absolute_anchor_path} (absolute: {parent_model._absolute_anchor_path.is_absolute()})"
        )

        # Save the parent model recursively
        parent_model.save(recurse=True)
        print(
            f"Unrelated - After save - Child model filepath: {child_model.filepath} (absolute: {child_model.filepath.is_absolute()})"
        )
        print(
            f"Unrelated - After save - Child model save_location: {child_model.save_location} (absolute: {child_model.save_location.is_absolute()})"
        )
        print(
            f"Unrelated - After save - Child model _absolute_anchor_path: {child_model._absolute_anchor_path} (absolute: {child_model._absolute_anchor_path.is_absolute()})"
        )
        print(
            f"Unrelated - After save - Parent model filepath: {parent_model.filepath} (absolute: {parent_model.filepath.is_absolute()})"
        )
        print(
            f"Unrelated - After save - Parent model save_location: {parent_model.save_location} (absolute: {parent_model.save_location.is_absolute()})"
        )
        print(
            f"Unrelated - After save - Parent model _absolute_anchor_path: {parent_model._absolute_anchor_path} (absolute: {parent_model._absolute_anchor_path.is_absolute()})"
        )

        # Verify the parent file was created
        self.assertTrue(parent_save_path.exists())

        # Verify the child file was NOT created, because it's not linked to the parent
        self.assertFalse(child_save_path.exists())

        # Now save the child model directly
        child_model.save()
        print(
            f"Unrelated - After direct save - Child model filepath: {child_model.filepath} (absolute: {child_model.filepath.is_absolute()})"
        )
        print(
            f"Unrelated - After direct save - Child model save_location: {child_model.save_location} (absolute: {child_model.save_location.is_absolute()})"
        )
        print(
            f"Unrelated - After direct save - Child model _absolute_anchor_path: {child_model._absolute_anchor_path} (absolute: {child_model._absolute_anchor_path.is_absolute()})"
        )

        # Verify the child file was created now
        self.assertTrue(child_save_path.exists())

        # Load the files again to verify their contents
        loaded_parent = SimpleFileModel(filepath=parent_save_path)
        loaded_child = SimpleFileModel(filepath=child_save_path)

        # Verify the loaded models' attributes
        self.assertEqual(loaded_parent.name, "parent_save")
        self.assertEqual(loaded_parent.value, 200)
        self.assertEqual(loaded_child.name, "child_save")
        self.assertEqual(loaded_child.value, 100)
        self.assertEqual(loaded_child.description, "Child model")

    def test_nested_path_resolution(self):
        """Test resolution of nested file paths.

        This test verifies that a FileModel can resolve paths to files in nested directories.

        The expected behavior:
            the model can load files from nested directories correctly.
        """
        parent_path = self.temp_dir / "parent_with_nested_child.txt"

        parent_model = SimpleFileModel(filepath=parent_path)

        self.assertEqual(parent_model.name, "parent_with_nested_child")
        self.assertEqual(parent_model.value, 25)
        self.assertIsNotNone(parent_model.child_file)
        self.assertEqual(parent_model.child_file.name, "nested_file")
        self.assertEqual(parent_model.child_file.value, 20)
        self.assertEqual(parent_model.child_file.description, "This file is in a nested directory")

    def test_multiple_children(self):
        """Test loading a file with multiple child references.

        This test verifies that a FileModel can load multiple child models.
        The expected behavior is that all child models are loaded correctly.
        """
        # Path to the parent file with multiple children
        parent_path = self.temp_dir / "parent_with_multiple_children.txt"

        # Load the parent file
        parent_model = SimpleFileModel(filepath=parent_path)

        # Verify the parent model's attributes
        self.assertEqual(parent_model.name, "parent_with_multiple_children")
        self.assertEqual(parent_model.value, 30)

        # Verify all child models were loaded
        self.assertIsNotNone(parent_model.child_file1)
        self.assertEqual(parent_model.child_file1.name, "simple_file")
        self.assertEqual(parent_model.child_file1.value, 10)

        self.assertIsNotNone(parent_model.child_file2)
        self.assertEqual(parent_model.child_file2.name, "mixed_case_file")
        self.assertEqual(parent_model.child_file2.value, 15)

        self.assertIsNotNone(parent_model.child_file3)
        self.assertEqual(parent_model.child_file3.name, "nested_file")
        self.assertEqual(parent_model.child_file3.value, 20)