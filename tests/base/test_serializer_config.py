import unittest
from unittest.mock import MagicMock, patch

import pytest

from hydrolib.core.base.models import SerializerConfig


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

    def test_update_float_format(self):
        """Test updating float_format after initialization."""
        config = SerializerConfig()
        config.float_format = ".3f"
        self.assertEqual(config.float_format, ".3f")

    def test_dict_method(self):
        """Test dict method returns correct dictionary."""
        config = SerializerConfig(float_format=".4f")
        result = config.dict()
        self.assertIn("float_format", result)
        self.assertEqual(result["float_format"], ".4f")

    def test_equality(self):
        """Test equality comparison between SerializerConfig instances."""
        config1 = SerializerConfig(float_format=".2f")
        config2 = SerializerConfig(float_format=".2f")
        config3 = SerializerConfig(float_format=".3f")
        
        self.assertEqual(config1, config2)
        self.assertNotEqual(config1, config3)

    def test_copy(self):
        """Test copying a SerializerConfig instance."""
        config = SerializerConfig(float_format=".5f")
        config_copy = config.copy()
        
        # Verify it's a different instance but with the same values
        self.assertIsNot(config, config_copy)
        self.assertEqual(config.float_format, config_copy.float_format)
        
        # Verify changing the copy doesn't affect the original
        config_copy.float_format = ".6f"
        self.assertEqual(config.float_format, ".5f")
        self.assertEqual(config_copy.float_format, ".6f")


if __name__ == "__main__":
    unittest.main()