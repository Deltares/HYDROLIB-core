from types import MethodType
from unittest.mock import MagicMock

import pytest

from hydrolib.tools.extforce_convert.mdu_parser import MDUParser


class TestMDUParserGetKeyword:
    """
    Unit tests for MDUParser.get_keyword method.

    Tests the behavior of the get_keyword method which retrieves the value
    of a specified keyword from the MDU file content.
    """

    @pytest.mark.unit
    def test_get_keyword_when_keyword_exists(self):
        """
        Test that get_keyword returns the correct value when the keyword exists.

        This test verifies that when a keyword is present in the MDU file content,
        the get_keyword method returns the associated value correctly.
        """
        parser = MagicMock(spec=MDUParser)
        parser.get_keyword = MethodType(MDUParser.get_keyword, parser)
        parser.find_keyword_lines = MethodType(
            MDUParser.find_keyword_lines, parser
        )
        parser.content = [
            "[general]\n",
            "Name = TestModel\n",
            "PathsRelativeToParent = 1\n",
        ]

        result = parser.get_keyword("PathsRelativeToParent")
        assert result == "1"

    @pytest.mark.unit
    def test_get_keyword_when_keyword_does_not_exist(self):
        """
        Test that get_keyword returns None when the keyword does not exist.

        This test verifies that when a keyword is not found in the MDU file content,
        the get_keyword method returns None.
        """
        parser = MagicMock(spec=MDUParser)
        parser.get_keyword = MethodType(MDUParser.get_keyword, parser)
        parser.find_keyword_lines = MethodType(
            MDUParser.find_keyword_lines, parser
        )
        parser.content = [
            "[general]\n",
            "Name = TestModel\n",
        ]

        result = parser.get_keyword("PathsRelativeToParent")
        assert result is None

    @pytest.mark.unit
    def test_get_keyword_with_empty_value(self):
        """
        Test that get_keyword returns None when the keyword has an empty value.

        This test verifies that when a keyword exists but has no value (empty string after =),
        the get_keyword method returns "".
        """
        parser = MagicMock(spec=MDUParser)
        parser.get_keyword = MethodType(MDUParser.get_keyword, parser)
        parser.find_keyword_lines = MethodType(
            MDUParser.find_keyword_lines, parser
        )
        parser.content = [
            "[general]\n",
            "Name = TestModel\n",
            "PathsRelativeToParent = \n",
        ]

        result = parser.get_keyword("PathsRelativeToParent")
        assert result is ""

    @pytest.mark.unit
    def test_get_keyword_with_comment(self):
        """
        Test that get_keyword extracts value correctly when line contains comment.

        This test verifies that when a keyword line contains a comment after the value,
        the get_keyword method returns only the value, excluding the comment.
        """
        parser = MagicMock(spec=MDUParser)
        parser.get_keyword = MethodType(MDUParser.get_keyword, parser)
        parser.find_keyword_lines = MethodType(
            MDUParser.find_keyword_lines, parser
        )
        parser.content = [
            "[general]\n",
            "PathsRelativeToParent = 1 # Use parent-relative paths\n",
        ]

        result = parser.get_keyword("PathsRelativeToParent")
        assert result == "1"

    @pytest.mark.unit
    def test_get_keyword_case_insensitive(self):
        """
        Test that get_keyword is case-insensitive when searching for keywords.

        This test verifies that the get_keyword method can find keywords regardless
        of the case used in the search string.
        """
        parser = MagicMock(spec=MDUParser)
        parser.get_keyword = MethodType(MDUParser.get_keyword, parser)
        parser.find_keyword_lines = MethodType(
            MDUParser.find_keyword_lines, parser
        )
        parser.content = [
            "[general]\n",
            "PathsRelativeToParent = 1\n",
        ]

        result = parser.get_keyword("pathsrelativetoparent")
        assert result == "1"


class TestMDUParserIsRelativeToParent:
    """
    Unit tests for MDUParser.is_relative_to_parent property.

    Tests the behavior of the is_relative_to_parent property which determines
    whether file paths in the MDU file are relative to the parent file or the MDU file itself.
    """

    @pytest.mark.unit
    def test_is_relative_to_parent_when_value_is_one(self):
        """
        Test that is_relative_to_parent returns True when PathsRelativeToParent = 1.

        This test verifies that when PathsRelativeToParent is set to "1" in the MDU file,
        the is_relative_to_parent property returns True, indicating paths are relative
        to the parent file.
        """
        parser = MagicMock(spec=MDUParser)
        parser.is_relative_to_parent = property(
            lambda self: MDUParser.is_relative_to_parent.fget(self)
        )
        parser.get_keyword = MethodType(MDUParser.get_keyword, parser)
        parser.find_keyword_lines = MethodType(
            MDUParser.find_keyword_lines, parser
        )
        parser.content = [
            "[general]\n",
            "PathsRelativeToParent = 1\n",
        ]

        result = MDUParser.is_relative_to_parent.fget(parser)
        assert result is True

    @pytest.mark.unit
    def test_is_relative_to_parent_when_value_is_zero(self):
        """
        Test that is_relative_to_parent returns False when PathsRelativeToParent = 0.

        This test verifies that when PathsRelativeToParent is set to "0" in the MDU file,
        the is_relative_to_parent property returns False, indicating paths are relative
        to the MDU file itself.
        """
        parser = MagicMock(spec=MDUParser)
        parser.get_keyword = MethodType(MDUParser.get_keyword, parser)
        parser.find_keyword_lines = MethodType(
            MDUParser.find_keyword_lines, parser
        )
        parser.content = [
            "[general]\n",
            "PathsRelativeToParent = 0\n",
        ]

        result = MDUParser.is_relative_to_parent.fget(parser)
        assert result is False

    @pytest.mark.unit
    def test_is_relative_to_parent_when_keyword_does_not_exist(self):
        """
        Test that is_relative_to_parent returns False when PathsRelativeToParent is not present.

        This test verifies that when the PathsRelativeToParent keyword is not found in
        the MDU file, the is_relative_to_parent property returns False (the default behavior).
        """
        parser = MagicMock(spec=MDUParser)
        parser.get_keyword = MethodType(MDUParser.get_keyword, parser)
        parser.find_keyword_lines = MethodType(
            MDUParser.find_keyword_lines, parser
        )
        parser.content = [
            "[general]\n",
            "Name = TestModel\n",
        ]

        result = MDUParser.is_relative_to_parent.fget(parser)
        assert result is False

    @pytest.mark.unit
    def test_is_relative_to_parent_when_value_is_empty(self):
        """
        Test that is_relative_to_parent returns False when PathsRelativeToParent has empty value.

        This test verifies that when the PathsRelativeToParent keyword exists but has an
        empty value, the is_relative_to_parent property returns False (treating empty as default).
        """
        parser = MagicMock(spec=MDUParser)
        parser.get_keyword = MethodType(MDUParser.get_keyword, parser)
        parser.find_keyword_lines = MethodType(
            MDUParser.find_keyword_lines, parser
        )
        parser.content = [
            "[general]\n",
            "PathsRelativeToParent = \n",
        ]

        result = MDUParser.is_relative_to_parent.fget(parser)
        assert result is False

    @pytest.mark.unit
    def test_is_relative_to_parent_when_value_is_non_standard(self):
        """
        Test that is_relative_to_parent returns False when PathsRelativeToParent has non-standard value.

        This test verifies that when the PathsRelativeToParent keyword has a value other than
        "1" (e.g., "2", "yes", etc.), the is_relative_to_parent property returns False,
        treating any non-"1" value as False.
        """
        parser = MagicMock(spec=MDUParser)
        parser.get_keyword = MethodType(MDUParser.get_keyword, parser)
        parser.find_keyword_lines = MethodType(
            MDUParser.find_keyword_lines, parser
        )
        parser.content = [
            "[general]\n",
            "PathsRelativeToParent = 2\n",
        ]

        result = MDUParser.is_relative_to_parent.fget(parser)
        assert result is False
