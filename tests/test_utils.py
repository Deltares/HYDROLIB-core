from pathlib import Path

import pytest

from hydrolib.core.io.dflowfm.mdu.models import Geometry, Output
from hydrolib.core.utils import get_substring_between, str_is_empty_or_none

from .utils import test_input_dir


class TestSplitString:
    def test_split_string_strip_whitespace(self):
        string_with_multiple_floats = "1.0     5.0"
        output = Output(statsinterval=string_with_multiple_floats)

        assert output.statsinterval == [1.0, 5.0]

    def test_split_string_strip_semicolon(self):
        e02 = test_input_dir / "e02"

        file1 = (
            e02 / "c11_korte-woerden-1d" / "dimr_model" / "dflowfm" / "structures.ini"
        )

        file2 = (
            e02
            / "f152_1d2d_projectmodels_rhu"
            / "c04_DHydamo-MGB-initialisation"
            / "fm"
            / "structure.ini"
        )

        string_with_multiple_files = f"{file1} ; {file2}"
        output = Geometry(structurefile=string_with_multiple_files)

        assert output.structurefile[0].filepath == Path(file1)
        assert output.structurefile[1].filepath == Path(file2)


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
