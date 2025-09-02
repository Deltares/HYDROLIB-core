from unittest.mock import patch

import pytest
from hydrolib.tools.extforce_convert.utils import CONVERTER_DATA
from hydrolib.tools.extforce_convert.mdu_parser import MDUParser


class TestMDUParserDeleteLine:
    """
    Unit tests for MDUParser.delete_line method covering all possible scenarios and edge cases.
    """

    @pytest.fixture(autouse=True)
    def setup_mduparser(self):
        # Patch file reading, FMModel loading, and Path.exists to avoid file IO and file existence checks
        with (
            patch.object(
                MDUParser,
                "_read_file",
                return_value=[
                    "Keyword1= value1\n",
                    "Keyword2= value2\n",
                    "Keyword3= value3\n",
                    "# Comment line\n",
                    "[Section]\n",
                ],
            ),
            patch.object(
                MDUParser,
                "_load_with_fm_model",
                return_value={
                    "external_forcing": {},
                    "geometry": {},
                    "time": {},
                    "physics": {"temperature": 0, "salinity": False},
                },
            ),
            patch("pathlib.Path.exists", return_value=True),
        ):
            self.parser = MDUParser("dummy_path.mdu")
        yield

    def test_delete_by_valid_index(self):
        """
        Test deleting a line by a valid index.
        Input: index=1 (second line)
        Expected: Line at index 1 is removed, content length decreases by 1.
        """
        initial_len = len(self.parser.content)
        self.parser.delete_line(index=1)
        assert len(self.parser.content) == initial_len - 1
        assert "Keyword2= value2\n" not in self.parser.content

    def test_delete_by_invalid_index_negative(self):
        """
        Test deleting a line by a negative index.
        Input: index=-1
        Expected: Raises IndexError.
        """
        with pytest.raises(IndexError):
            self.parser.delete_line(index=-1)

    def test_delete_by_invalid_index_out_of_bounds(self):
        """
        Test deleting a line by an out-of-bounds index.
        Input: index=100
        Expected: Raises IndexError.
        """
        with pytest.raises(IndexError):
            self.parser.delete_line(index=100)

    def test_delete_by_valid_keyword_present(self):
        """
        Test deleting a line by a keyword that is present.
        Input: keyword="Keyword3"
        Expected: Line containing the keyword is removed, content length decreases by 1.
        """
        initial_len = len(self.parser.content)
        self.parser.delete_line(keyword="Keyword3")
        assert len(self.parser.content) == initial_len - 1
        assert not any(line.startswith("Keyword3") for line in self.parser.content)

    def test_delete_by_valid_keyword_not_present(self):
        """
        Test deleting a line by a keyword that is not present.
        Input: keyword="NotPresent"
        Expected: No change to content, no error raised.
        """
        initial_len = len(self.parser.content)
        self.parser.delete_line(keyword="NotPresent")
        assert len(self.parser.content) == initial_len

    def test_delete_by_keyword_empty_string(self):
        """
        Test deleting a line by an empty string keyword.
        Input: keyword=""
        Expected: Raises ValueError.
        """
        with pytest.raises(ValueError):
            self.parser.delete_line(keyword="")

    def test_delete_by_keyword_case_sensitive_match(self):
        """
        Test deleting a line by a keyword with case sensitivity enabled and matching case.
        Input: keyword="Keyword2", case_sensitive=True
        Expected: Line is removed.
        """
        initial_len = len(self.parser.content)
        self.parser.delete_line(keyword="Keyword2", case_sensitive=True)
        assert len(self.parser.content) == initial_len - 1
        assert not any(line.startswith("Keyword2") for line in self.parser.content)

    def test_delete_by_keyword_case_sensitive_no_match(self):
        """
        Test deleting a line by a keyword with case sensitivity enabled and non-matching case.
        Input: keyword="keyword2", case_sensitive=True
        Expected: No change to content, no error raised.
        """
        initial_len = len(self.parser.content)
        self.parser.delete_line(keyword="keyword2", case_sensitive=True)
        assert len(self.parser.content) == initial_len

    def test_delete_with_both_index_and_keyword(self):
        """
        Test deleting a line with both index and keyword provided.
        Input: index=1, keyword="Keyword2"
        Expected: Raises ValueError.
        """
        with pytest.raises(ValueError):
            self.parser.delete_line(index=1, keyword="Keyword2")

    def test_delete_with_neither_index_nor_keyword(self):
        """
        Test deleting a line with neither index nor keyword provided.
        Input: index=None, keyword=None
        Expected: Raises ValueError.
        """
        with pytest.raises(ValueError):
            self.parser.delete_line()


class TestMDUParserClean:
    @pytest.fixture(autouse=True)
    def setup_parser(self):
        self.deprecated_keys = CONVERTER_DATA.get("mdu").get("deprecated-key-words")
        yield

    def _make_parser(self, lines):
        with (
            patch.object(MDUParser, "_read_file", return_value=lines),
            patch.object(
                MDUParser,
                "_load_with_fm_model",
                return_value={
                    "external_forcing": {},
                    "geometry": {},
                    "time": {},
                    "physics": {"temperature": 0, "salinity": False},
                },
            ),
            patch("pathlib.Path.exists", return_value=True),
        ):
            return MDUParser("dummy_path.mdu")

    def test_clean_all_deprecated_present(self):
        """
        the test adds all the deprecated keywords to the content and checks that they are all removed, and only the
        last line is left.
        """
        lines = [f"{key}= value\n" for key in self.deprecated_keys] + ["Other= value\n"]
        parser = self._make_parser(lines)
        parser.clean()
        assert all(key not in "".join(parser.content) for key in self.deprecated_keys)
        assert "Other= value\n" in parser.content

    def test_clean_some_deprecated_present(self):
        """
        the test adds only one deprecated keyword to the content and checks that it is removed.
        """
        lines = [f"{self.deprecated_keys[0]}= value\n", "Other= value\n"]
        parser = self._make_parser(lines)
        parser.clean()
        assert self.deprecated_keys[0] not in "".join(parser.content)
        assert "Other= value\n" in parser.content

    def test_clean_none_deprecated_present(self):
        lines = ["Keyword1= value\n", "Keyword2= value\n"]
        parser = self._make_parser(lines)
        parser.clean()
        assert parser.content == lines

    def test_clean_case_insensitive(self):
        """
        Use different case for deprecated keyword
        """
        lines = [f"{self.deprecated_keys[0].upper()}= value\n", "Other= value\n"]
        parser = self._make_parser(lines)
        parser.clean()
        assert self.deprecated_keys[0].upper() not in "".join(parser.content)
        assert "Other= value\n" in parser.content

    def test_clean_only_deprecated_keywords(self):
        lines = [f"{key}= value\n" for key in self.deprecated_keys]
        parser = self._make_parser(lines)
        parser.clean()
        assert parser.content == []

    def test_clean_with_comments_and_sections(self):
        lines = [
            "# Comment\n",
            "[Section]\n",
            f"{self.deprecated_keys[0]}= value\n",
            "Other= value\n",
        ]
        parser = self._make_parser(lines)
        parser.clean()
        assert "# Comment\n" in parser.content
        assert "[Section]\n" in parser.content
        assert "Other= value\n" in parser.content
        assert self.deprecated_keys[0] not in "".join(parser.content)
