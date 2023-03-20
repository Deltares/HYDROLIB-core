from math import nan

import pytest
from pydantic.error_wrappers import ValidationError

from hydrolib.core.dflowfm.ini.models import DataBlockINIBasedModel

from ...utils import error_occurs_only_once


class TestDataBlockINIBasedModel:
    def test_datablock_with_nan_values_should_raise_error(self):
        model = DataBlockINIBasedModel()

        with pytest.raises(ValidationError) as error:
            model.datablock = [[nan, 0], [-1, 2]]

        expected_message = "NaN is not supported in datablocks."
        assert expected_message in str(error.value)

    def test_updating_datablock_with_nan_values_should_raise_error(self):
        model = DataBlockINIBasedModel()

        valid_datablock = [[0, 1], [2, 3]]
        model.datablock = valid_datablock

        invalid_datablock = [[nan, 1], [2, 3]]
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
