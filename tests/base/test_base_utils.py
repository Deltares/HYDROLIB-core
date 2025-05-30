import unittest
from operator import eq, ge, gt, le, lt, ne
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from hydrolib.core.base.utils import (
    FileChecksumCalculator,
    FilePathStyleConverter,
    FortranScientificNotationConverter,
    FortranUtils,
    OperatingSystem,
    PathStyle,
    get_operating_system,
    get_path_style_for_current_operating_system,
    get_str_len,
    get_substring_between,
    operator_str,
    str_is_empty_or_none,
    to_key,
    to_list,
)


class TestToKey(unittest.TestCase):
    """Test cases for the to_key function."""

    def test_to_key_with_simple_string(self):
        """Test to_key function with a simple string."""
        result = to_key("test")
        self.assertEqual(result, "test")

    def test_to_key_with_spaces(self):
        """Test to_key function with spaces."""
        result = to_key("test string")
        self.assertEqual(result, "test_string")

    def test_to_key_with_hyphens(self):
        """Test to_key function with hyphens."""
        result = to_key("test-string")
        self.assertEqual(result, "teststring")

    def test_to_key_with_mixed_case(self):
        """Test to_key function with mixed case."""
        result = to_key("TestString")
        self.assertEqual(result, "teststring")

    def test_to_key_with_leading_digits(self):
        """Test to_key function with leading digits."""
        result = to_key("123test")
        self.assertEqual(result, "onetwothreetest")

    def test_to_key_with_leading_digits_and_spaces(self):
        """Test to_key function with leading digits and spaces."""
        result = to_key("123 test string")
        self.assertEqual(result, "onetwothree_test_string")

    def test_to_key_with_all_digits(self):
        """Test to_key function with all digits."""
        result = to_key("12345")
        self.assertEqual(result, "onetwothreefourfive")

    def test_to_key_with_mixed_characters(self):
        """Test to_key function with mixed characters."""
        result = to_key("123-Test String")
        self.assertEqual(result, "onetwothreetest_string")


class TestToList(unittest.TestCase):
    """Test cases for the to_list function."""

    def test_to_list_with_non_list(self):
        """Test to_list function with a non-list item."""
        result = to_list("test")
        self.assertEqual(result, ["test"])

    def test_to_list_with_list(self):
        """Test to_list function with a list."""
        test_list = ["test1", "test2"]
        result = to_list(test_list)
        self.assertEqual(result, test_list)

    def test_to_list_with_empty_list(self):
        """Test to_list function with an empty list."""
        test_list = []
        result = to_list(test_list)
        self.assertEqual(result, test_list)

    def test_to_list_with_none(self):
        """Test to_list function with None."""
        result = to_list(None)
        self.assertEqual(result, [None])

    def test_to_list_with_dict(self):
        """Test to_list function with a dictionary."""
        test_dict = {"key": "value"}
        result = to_list(test_dict)
        self.assertEqual(result, [test_dict])

    def test_to_list_with_number(self):
        """Test to_list function with a number."""
        result = to_list(42)
        self.assertEqual(result, [42])


class TestStrIsEmptyOrNone(unittest.TestCase):
    """Test cases for the str_is_empty_or_none function."""

    def test_str_is_empty_or_none_with_none(self):
        """Test str_is_empty_or_none function with None."""
        result = str_is_empty_or_none(None)
        self.assertTrue(result)

    def test_str_is_empty_or_none_with_empty_string(self):
        """Test str_is_empty_or_none function with an empty string."""
        result = str_is_empty_or_none("")
        self.assertTrue(result)

    def test_str_is_empty_or_none_with_whitespace(self):
        """Test str_is_empty_or_none function with whitespace."""
        result = str_is_empty_or_none("   ")
        self.assertTrue(result)

    def test_str_is_empty_or_none_with_non_empty_string(self):
        """Test str_is_empty_or_none function with a non-empty string."""
        result = str_is_empty_or_none("test")
        self.assertFalse(result)

    def test_str_is_empty_or_none_with_string_with_content_and_spaces(self):
        """Test str_is_empty_or_none function with a string containing content and spaces."""
        result = str_is_empty_or_none("  test  ")
        self.assertFalse(result)


class TestGetStrLen(unittest.TestCase):
    """Test cases for the get_str_len function."""

    def test_get_str_len_with_none(self):
        """Test get_str_len function with None."""
        result = get_str_len(None)
        self.assertEqual(result, 0)

    def test_get_str_len_with_empty_string(self):
        """Test get_str_len function with an empty string."""
        result = get_str_len("")
        self.assertEqual(result, 0)

    def test_get_str_len_with_non_empty_string(self):
        """Test get_str_len function with a non-empty string."""
        result = get_str_len("test")
        self.assertEqual(result, 4)

    def test_get_str_len_with_whitespace(self):
        """Test get_str_len function with whitespace."""
        result = get_str_len("   ")
        self.assertEqual(result, 3)


class TestGetSubstringBetween(unittest.TestCase):
    """Test cases for the get_substring_between function."""

    def test_get_substring_between_with_valid_input(self):
        """Test get_substring_between function with valid input."""
        source = "This is a [test] string"
        result = get_substring_between(source, "[", "]")
        self.assertEqual(result, "test")

    def test_get_substring_between_with_multiple_occurrences(self):
        """Test get_substring_between function with multiple occurrences of start and end."""
        source = "This is a [test] string with [another] test"
        result = get_substring_between(source, "[", "]")
        self.assertEqual(result, "test] string with [another")

    def test_get_substring_between_with_missing_start(self):
        """Test get_substring_between function with missing start string."""
        source = "This is a test string"
        result = get_substring_between(source, "[", "]")
        self.assertIsNone(result)

    def test_get_substring_between_with_missing_end(self):
        """Test get_substring_between function with missing end string."""
        source = "This is a [test string"
        result = get_substring_between(source, "[", "]")
        self.assertIsNone(result)

    def test_get_substring_between_with_empty_source(self):
        """Test get_substring_between function with empty source string."""
        source = ""
        result = get_substring_between(source, "[", "]")
        self.assertIsNone(result)

    def test_get_substring_between_with_empty_result(self):
        """Test get_substring_between function with empty result."""
        source = "This is a [] string"
        result = get_substring_between(source, "[", "]")
        self.assertEqual(result, "")


class TestOperatorStr(unittest.TestCase):
    """Test cases for the operator_str function."""

    def test_operator_str_with_eq(self):
        """Test operator_str function with eq operator."""
        result = operator_str(eq)
        self.assertEqual(result, "is")

    def test_operator_str_with_ne(self):
        """Test operator_str function with ne operator."""
        result = operator_str(ne)
        self.assertEqual(result, "is not")

    def test_operator_str_with_lt(self):
        """Test operator_str function with lt operator."""
        result = operator_str(lt)
        self.assertEqual(result, "is less than")

    def test_operator_str_with_le(self):
        """Test operator_str function with le operator."""
        result = operator_str(le)
        self.assertEqual(result, "is less than or equal to")

    def test_operator_str_with_gt(self):
        """Test operator_str function with gt operator."""
        result = operator_str(gt)
        self.assertEqual(result, "is greater than")

    def test_operator_str_with_ge(self):
        """Test operator_str function with ge operator."""
        result = operator_str(ge)
        self.assertEqual(result, "is greater than or equal to")

    def test_operator_str_with_unsupported_operator(self):
        """Test operator_str function with an unsupported operator."""

        def custom_operator(a, b):
            return a + b

        result = operator_str(custom_operator)
        self.assertEqual(result, str(custom_operator))


class TestOperatingSystem(unittest.TestCase):
    """Test cases for the OperatingSystem enum."""

    def test_operating_system_values(self):
        """Test OperatingSystem enum values."""
        self.assertIsInstance(OperatingSystem.WINDOWS, OperatingSystem)
        self.assertIsInstance(OperatingSystem.LINUX, OperatingSystem)
        self.assertIsInstance(OperatingSystem.MACOS, OperatingSystem)


class TestGetOperatingSystem(unittest.TestCase):
    """Test cases for the get_operating_system function."""

    def test_get_operating_system_windows(self):
        """Test get_operating_system function on Windows."""
        with patch("platform.system", return_value="Windows"):
            result = get_operating_system()
            self.assertEqual(result, OperatingSystem.WINDOWS)

    def test_get_operating_system_linux(self):
        """Test get_operating_system function on Linux."""
        with patch("platform.system", return_value="Linux"):
            result = get_operating_system()
            self.assertEqual(result, OperatingSystem.LINUX)

    def test_get_operating_system_macos(self):
        """Test get_operating_system function on MacOS."""
        with patch("platform.system", return_value="Darwin"):
            result = get_operating_system()
            self.assertEqual(result, OperatingSystem.MACOS)

    def test_get_operating_system_unsupported(self):
        """Test get_operating_system function on an unsupported OS."""
        with patch("platform.system", return_value="Unsupported"):
            with self.assertRaises(NotImplementedError):
                get_operating_system()


class TestPathStyle(unittest.TestCase):
    """Test cases for the PathStyle enum."""

    def test_path_style_values(self):
        """Test PathStyle enum values."""
        self.assertEqual(PathStyle.UNIXLIKE, "unix")
        self.assertEqual(PathStyle.WINDOWSLIKE, "windows")


class TestGetPathStyleForCurrentOperatingSystem(unittest.TestCase):
    """Test cases for the get_path_style_for_current_operating_system function."""

    def test_get_path_style_for_windows(self):
        """Test get_path_style_for_current_operating_system function on Windows."""
        with patch(
            "hydrolib.core.base.utils.get_operating_system",
            return_value=OperatingSystem.WINDOWS,
        ):
            result = get_path_style_for_current_operating_system()
            self.assertEqual(result, PathStyle.WINDOWSLIKE)

    def test_get_path_style_for_linux(self):
        """Test get_path_style_for_current_operating_system function on Linux."""
        with patch(
            "hydrolib.core.base.utils.get_operating_system",
            return_value=OperatingSystem.LINUX,
        ):
            result = get_path_style_for_current_operating_system()
            self.assertEqual(result, PathStyle.UNIXLIKE)

    def test_get_path_style_for_macos(self):
        """Test get_path_style_for_current_operating_system function on MacOS."""
        with patch(
            "hydrolib.core.base.utils.get_operating_system",
            return_value=OperatingSystem.MACOS,
        ):
            result = get_path_style_for_current_operating_system()
            self.assertEqual(result, PathStyle.UNIXLIKE)


class TestFilePathStyleConverter(unittest.TestCase):
    """Test cases for the FilePathStyleConverter class."""

    def setUp(self):
        """Set up test fixtures."""
        self.converter = FilePathStyleConverter()

    def test_convert_to_os_style_same_style(self):
        """Test convert_to_os_style method when source and target styles are the same."""
        with patch(
            "hydrolib.core.base.utils.get_path_style_for_current_operating_system",
            return_value=PathStyle.UNIXLIKE,
        ):
            # Recreate converter with mocked OS style
            self.converter = FilePathStyleConverter()
            # When using Path("/test/path"), it's interpreted as a Windows path with drive "test:"
            # So we need to use a different path for testing
            result = self.converter.convert_to_os_style(
                Path("test/path"), PathStyle.UNIXLIKE
            )
            self.assertEqual(result, "test/path")

    def test_convert_to_os_style_unix_to_windows(self):
        """Test convert_to_os_style method when converting from Unix to Windows style."""
        with patch(
            "hydrolib.core.base.utils.get_path_style_for_current_operating_system",
            return_value=PathStyle.WINDOWSLIKE,
        ):
            # Recreate converter with mocked OS style
            self.converter = FilePathStyleConverter()
            result = self.converter.convert_to_os_style(
                Path("/c/test/path"), PathStyle.UNIXLIKE
            )
            self.assertEqual(result, "c:/test/path")

    def test_convert_to_os_style_windows_to_unix(self):
        """Test convert_to_os_style method when converting from Windows to Unix style."""
        with patch(
            "hydrolib.core.base.utils.get_path_style_for_current_operating_system",
            return_value=PathStyle.UNIXLIKE,
        ):
            # Recreate converter with mocked OS style
            self.converter = FilePathStyleConverter()
            # The actual implementation returns the Windows path converted to Unix format
            result = self.converter.convert_to_os_style(
                Path("c:/test/path"), PathStyle.WINDOWSLIKE
            )
            # The mocking is now working as expected, and the path is correctly converted
            self.assertEqual(result, "/c/test/path")

    def test_convert_to_os_style_relative_path(self):
        """Test convert_to_os_style method with a relative path."""
        result = self.converter.convert_to_os_style(
            Path("test/path"), PathStyle.UNIXLIKE
        )
        self.assertEqual(result, "test/path")

    def test_convert_from_os_style_same_style(self):
        """Test convert_from_os_style method when source and target styles are the same."""
        with patch(
            "hydrolib.core.base.utils.get_path_style_for_current_operating_system",
            return_value=PathStyle.UNIXLIKE,
        ):
            # Recreate converter with mocked OS style
            self.converter = FilePathStyleConverter()
            result = self.converter.convert_from_os_style(
                Path("/test/path"), PathStyle.UNIXLIKE
            )
            self.assertEqual(result, "/test/path")

    def test_convert_from_os_style_unix_to_windows(self):
        """Test convert_from_os_style method when converting from Unix to Windows style."""
        with patch(
            "hydrolib.core.base.utils.get_path_style_for_current_operating_system",
            return_value=PathStyle.UNIXLIKE,
        ):
            # Recreate converter with mocked OS style
            self.converter = FilePathStyleConverter()
            # The actual implementation converts from the OS style (UNIXLIKE) to the target style (WINDOWSLIKE)
            result = self.converter.convert_from_os_style(
                Path("/c/test/path"), PathStyle.WINDOWSLIKE
            )
            # The mocking is now working as expected, and the path is correctly converted
            self.assertEqual(result, "c:/test/path")

    def test_convert_from_os_style_windows_to_unix(self):
        """Test convert_from_os_style method when converting from Windows to Unix style."""
        with patch(
            "hydrolib.core.base.utils.get_path_style_for_current_operating_system",
            return_value=PathStyle.WINDOWSLIKE,
        ):
            # Recreate converter with mocked OS style
            self.converter = FilePathStyleConverter()
            result = self.converter.convert_from_os_style(
                Path("c:/test/path"), PathStyle.UNIXLIKE
            )
            self.assertEqual(result, "/c/test/path")

    def test_convert_from_os_style_relative_path(self):
        """Test convert_from_os_style method with a relative path."""
        result = self.converter.convert_from_os_style(
            Path("test/path"), PathStyle.UNIXLIKE
        )
        self.assertEqual(result, "test/path")

    def test_convert_unsupported_style(self):
        """Test _convert method with unsupported path styles."""
        with self.assertRaises(NotImplementedError):
            FilePathStyleConverter._convert(
                Path("/test/path"), "unsupported", PathStyle.UNIXLIKE
            )


class TestFileChecksumCalculator(unittest.TestCase):
    """Test cases for the FileChecksumCalculator class."""

    def test_calculate_checksum_existing_file(self):
        """Test calculate_checksum method with an existing file."""
        # Create a temporary file
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=True),
            patch(
                "hydrolib.core.base.utils.FileChecksumCalculator._calculate_md5_checksum",
                return_value="test_checksum",
            ),
        ):
            result = FileChecksumCalculator.calculate_checksum(Path("test_file.txt"))
            self.assertEqual(result, "test_checksum")

    def test_calculate_checksum_non_existing_file(self):
        """Test calculate_checksum method with a non-existing file."""
        with patch("pathlib.Path.exists", return_value=False):
            result = FileChecksumCalculator.calculate_checksum(
                Path("non_existing_file.txt")
            )
            self.assertIsNone(result)

    def test_calculate_checksum_directory(self):
        """Test calculate_checksum method with a directory."""
        with (
            patch("pathlib.Path.exists", return_value=True),
            patch("pathlib.Path.is_file", return_value=False),
        ):
            result = FileChecksumCalculator.calculate_checksum(Path("directory"))
            self.assertIsNone(result)

    def test_calculate_md5_checksum(self):
        """Test _calculate_md5_checksum method."""
        # Mock file content
        mock_file_content = b"test content"

        # Mock open function to return a file-like object with our content
        mock_file = MagicMock()
        mock_file.__enter__.return_value.read.side_effect = [mock_file_content, b""]

        with (
            patch("builtins.open", return_value=mock_file),
            patch(
                "hydrolib.core.base.utils.md5",
                return_value=MagicMock(hexdigest=lambda: "test_checksum"),
            ),
        ):
            result = FileChecksumCalculator._calculate_md5_checksum(
                Path("test_file.txt")
            )
            self.assertEqual(result, "test_checksum")


class TestFortranUtils(unittest.TestCase):
    """Test cases for the FortranUtils class."""

    def test_replace_fortran_scientific_notation_string(self):
        """Test replace_fortran_scientific_notation method with a string."""
        # Test with lowercase 'd'
        result = FortranUtils.replace_fortran_scientific_notation("1.0d-3")
        self.assertEqual(result, "1.0e-3")

        # Test with uppercase 'D'
        result = FortranUtils.replace_fortran_scientific_notation("1.0D+3")
        self.assertEqual(result, "1.0e+3")

        # Test with no exponent sign
        result = FortranUtils.replace_fortran_scientific_notation("1.0d3")
        self.assertEqual(result, "1.0e3")

        # Test with no decimal point
        result = FortranUtils.replace_fortran_scientific_notation("1d3")
        self.assertEqual(result, "1e3")

        # Test with regular string (no scientific notation)
        result = FortranUtils.replace_fortran_scientific_notation("regular string")
        self.assertEqual(result, "regular string")

    def test_replace_fortran_scientific_notation_list(self):
        """Test replace_fortran_scientific_notation method with a list."""
        test_list = ["1.0d-3", "2.0D+4", "regular string"]
        result = FortranUtils.replace_fortran_scientific_notation(test_list)
        self.assertEqual(result, ["1.0e-3", "2.0e+4", "regular string"])

    def test_replace_fortran_scientific_notation_other_types(self):
        """Test replace_fortran_scientific_notation method with other types."""
        # Test with an integer
        result = FortranUtils.replace_fortran_scientific_notation(42)
        self.assertEqual(result, 42)

        # Test with a float
        result = FortranUtils.replace_fortran_scientific_notation(3.14)
        self.assertEqual(result, 3.14)

        # Test with None
        result = FortranUtils.replace_fortran_scientific_notation(None)
        self.assertIsNone(result)

        # Test with a dictionary
        test_dict = {"key": "value"}
        result = FortranUtils.replace_fortran_scientific_notation(test_dict)
        self.assertEqual(result, test_dict)


class Test:
    class MockField:
        def __init__(self, annotation):
            self.annotation = annotation

    @pytest.mark.parametrize(
        "input_values,field_definitions,expected_output",
        [
            (
                {"a": "1.23D+03", "b": "text", "c": [1.0, "2.34D+02"]},
                {
                    "a": MockField(float),
                    "b": MockField(str),
                    "c": MockField(list[float]),
                },
                {"a": "1.23e+03", "b": "text", "c": [1.0, "2.34e+02"]},
            ),
            (
                {"a": "1.0E+02"},
                {"a": MockField(float)},
                {"a": "1.0E+02"},
            ),
            (
                {"a": ["1.0D+01", "2.0D+02"]},
                {"a": MockField(list[float])},
                {"a": ["1.0e+01", "2.0e+02"]},
            ),
            (
                {"a": "value"},
                {},
                {"a": "value"},
            ),
            (
                {"a": "value"},
                {"a": MockField(str)},
                {"a": "value"},
            ),
        ],
    )
    def test_convert_fortran_notation_fields(
        self, input_values, field_definitions, expected_output
    ):
        result = FortranScientificNotationConverter.convert_fields(
            input_values, field_definitions
        )
        assert result == expected_output
