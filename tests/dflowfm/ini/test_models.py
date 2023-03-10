from math import nan
from ...utils import error_occurs_only_once
from pydantic.error_wrappers import ValidationError
import pytest
from typing import Union

from hydrolib.core.dflowfm.ini.models import DataBlockINIBasedModel


class TestDataBlockINIBasedModel:
    @pytest.mark.parametrize(
        "nan_value",
        [
            pytest.param(nan),
            pytest.param("NAN"),
            pytest.param("nan"),
            pytest.param("nAn"),
        ],
    )
    def test_datablock_with_nan_values_should_raise_error(
        self, nan_value: Union[str, float]
    ):
        model = DataBlockINIBasedModel()

        with pytest.raises(ValidationError) as error:
            model.datablock = [[nan_value, 0], [-1, 2]]

        expected_message = "NaN is not supported in datablocks."
        assert expected_message in str(error.value)

    @pytest.mark.parametrize(
        "nan_value",
        [
            pytest.param(nan),
            pytest.param("NAN"),
            pytest.param("nan"),
            pytest.param("nAn"),
        ],
    )
    def test_updating_datablock_with_nan_values_should_raise_error(
        self, nan_value: Union[str, float]
    ):
        model = DataBlockINIBasedModel()

        valid_datablock = [[0, 1], [2, 3]]
        model.datablock = valid_datablock

        invalid_datablock = [[nan_value, 1], [2, 3]]
        with pytest.raises(ValidationError) as error:
            model.datablock = invalid_datablock

        expected_message = "NaN is not supported in datablocks."
        assert expected_message in str(error.value)

    def test_datablock_with_multiple_nans_should_only_give_error_once(self):
        model = DataBlockINIBasedModel()

        with pytest.raises(ValidationError) as error:
            model.datablock = [[nan, nan], [nan, nan]]

        expected_message = "NaN is not supported in datablocks."
        assert error_occurs_only_once(expected_message, str(error.value))
