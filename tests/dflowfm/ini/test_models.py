from math import nan
from typing import List

import pytest
from pydantic import ValidationError

from hydrolib.core.dflowfm.ini.models import DataBlockINIBasedModel, INIBasedModel
from tests.utils import error_occurs_only_once


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

    def test_as_dataframe(self):
        model = DataBlockINIBasedModel()

        valid_datablock = [[0, 1], [2, 3]]
        model.datablock = valid_datablock
        df = model.as_dataframe()
        assert df.loc[:, 0].to_list() == [1.0, 3.0]


class TestINIBasedModel:
    class INIBasedModelTest(INIBasedModel):
        id: str
        float_value: float
        float_values: List[float]

    _random_string: str = "randomString"
    _random_float: float = 123.456
    _random_list_of_floats: List[float] = [12.34, 56.78]

    @pytest.mark.parametrize("string_value", ["1d0", "1d-2", "1d+2", "1.d+2", "-1.d-2"])
    def test_scientific_notation_for_string_field_is_parsed_as_string(
        self, string_value: str
    ):

        test_model = self.INIBasedModelTest(
            id=string_value,
            float_value=self._random_float,
            float_values=self._random_list_of_floats,
        )

        assert test_model.id == string_value
        assert test_model.float_value == pytest.approx(self._random_float)
        assert test_model.float_values == pytest.approx(self._random_list_of_floats)

    @pytest.mark.parametrize(
        "float_as_string, expected_value",
        [
            ("1d0", 1e0),
            ("1d-2", 1e-2),
            ("1d+2", 1e2),
            ("1.d+2", 1.0e2),
            ("-1.d-2", -1.0e-2),
        ],
    )
    def test_scientific_notation_for_float_field_is_parsed_as_float(
        self, float_as_string: str, expected_value: float
    ):
        test_model = self.INIBasedModelTest(
            id=self._random_string,
            float_value=float_as_string,
            float_values=self._random_list_of_floats,
        )

        assert test_model.id == self._random_string
        assert test_model.float_value == pytest.approx(expected_value)
        assert test_model.float_values == pytest.approx(self._random_list_of_floats)

    @pytest.mark.parametrize(
        "floats_as_strings, expected_values",
        [
            (["1d0", "1d-2"], [1e0, 1e-2]),
            (["1d+2", "1.d+2", "-1.d-2"], [1e2, 1.0e2, -1.0e-2]),
        ],
    )
    def test_scientific_notation_for_list_of_float_field_is_parsed_as_list_of_floats(
        self, floats_as_strings: List[str], expected_values: List[float]
    ):
        test_model = self.INIBasedModelTest(
            id=self._random_string,
            float_value=self._random_float,
            float_values=floats_as_strings,
        )

        assert test_model.id == self._random_string
        assert test_model.float_value == pytest.approx(self._random_float)
        assert test_model.float_values == pytest.approx(expected_values)

    def test_setting_string_attribute_with_scientific_notation_correctly_parses_value(
        self,
    ):
        test_model = self.INIBasedModelTest(
            id=self._random_string,
            float_value=self._random_float,
            float_values=self._random_list_of_floats,
        )

        test_model.id = "1d1"

        assert test_model.id == "1d1"

    def test_setting_float_attribute_with_scientific_notation_correctly_parses_value(
        self,
    ):
        test_model = self.INIBasedModelTest(
            id=self._random_string,
            float_value=self._random_float,
            float_values=self._random_list_of_floats,
        )

        test_model.float_value = "1d1"

        assert test_model.float_value == pytest.approx(1e1)

    def test_setting_list_of_floats_attribute_with_scientific_notation_correctly_parses_values(
        self,
    ):
        test_model = self.INIBasedModelTest(
            id=self._random_string,
            float_value=self._random_float,
            float_values=self._random_list_of_floats,
        )

        test_model.float_values = ["1d1", "2d-1"]

        assert test_model.float_values == pytest.approx([1e1, 2e-1])
