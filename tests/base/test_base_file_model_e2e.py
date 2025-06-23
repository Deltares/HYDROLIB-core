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
                if key in ["child_file", "child_file1", "child_file2", "child_file3"] and isinstance(value, FileModel):
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
        self.temp_dir = Path(tempfile.mkdtemp())
        
        # Path to the test input files
        self.input_dir = Path("tests/data/input/base_file_model_tests")
        
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
        
        Removes the temporary directory.
        """
        # Remove the temporary directory
        shutil.rmtree(self.temp_dir)

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
        model = SimpleFileModel(name="test_save", value=42, description="Test save operation")

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
