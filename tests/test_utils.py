from pathlib import Path

import pytest

from hydrolib.core.io.mdu.models import Output
from hydrolib.core.utils import get_list_index_safely, str_is_empty_or_none


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


class TestGetListIndexSafely:
    @pytest.mark.parametrize(
        "list, item, start, end, exp_index",
        [
            pytest.param([0, 1, 2], 0, 0, 2, 0),
            pytest.param([0, 1, 2], 1, 0, 2, 1),
            pytest.param([0, 1, 2], 2, 0, 2, 2),
            pytest.param([0, 1, 2], 3, 0, 2, -1),
            pytest.param([0, 1, 2], 0, 0, 1, 0),
            pytest.param([0, 1, 2], 1, 0, 1, 1),
            pytest.param([0, 1, 2], 2, 0, 1, -1),
        ],
    )
    def test_get_item_index_expected_result(
        self, list: list, item, start: int, end: int, exp_index: int
    ):
        result = get_list_index_safely(list, item, start, end)

        assert result == exp_index
