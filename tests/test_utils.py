from pathlib import Path

import pytest

from hydrolib.core.io.mdu.models import Output
from hydrolib.core.utils import get_substring_between, str_is_empty_or_none


class TestSplitString:
    def test_split_string_strip_whitespace(self):
        string_with_multiple_floats = "1.0     5.0"
        output = Output(statsinterval=string_with_multiple_floats)

        assert output.statsinterval == [1.0, 5.0]

    def test_split_string_strip_semicolon(self):
        string_with_multiple_files = "file1 ; file2"
        output = Output(obsfile=string_with_multiple_files)

        assert output.obsfile == [Path("file1"), Path("file2")]


class TestStrIsEmptyOrNone:
    @pytest.mark.parametrize(
        "input_str",
        [
            pytest.param("", id="No spaces"),
            pytest.param(" ", id="Spaces"),
            pytest.param(None, id="None"),
            pytest.param("\t", id="Tabulator"),
        ],
    )
    def test_given_args_expected_result(self, input_str: str):
        assert str_is_empty_or_none(input_str)

    def test_given_valid_args_returns_true(self):
        assert str_is_empty_or_none("aValue") is False


class TestGetSubstringBetween:
    @pytest.mark.parametrize(
        "start, end, exp_result",
        [
            pytest.param("", "brown", "The quick "),
            pytest.param("brown", "lazy", " fox jumps over the "),
            pytest.param("lazy", "brown", None),
            pytest.param("brown", "cat", None),
        ],
    )
    def test_get_substring_between_expected_result(
        self, start: str, end: str, exp_result: str
    ):
        source = "The quick brown fox jumps over the lazy dog"
        result = get_substring_between(source, start, end)

        assert result == exp_result
