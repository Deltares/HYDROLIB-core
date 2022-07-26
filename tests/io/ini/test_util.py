from typing import Dict, List, Optional

import pytest
from pydantic.error_wrappers import ValidationError

from hydrolib.core.io.ini.models import INIBasedModel
from hydrolib.core.io.ini.util import get_number_of_coordinates_validator


class TestCoordinatesValidator:
    class DummyModel(INIBasedModel):
        """Dummy model to test the validation of the number of coordinates."""

        numcoordinates: Optional[int]
        xcoordinates: Optional[List[float]]
        ycoordinates: Optional[List[float]]

        _number_of_coordinates_validator = get_number_of_coordinates_validator(
            minimum_required_number_of_coordinates=2
        )

    def test_all_values_none_does_not_throw(self):
        model = TestCoordinatesValidator.DummyModel()

        assert model.numcoordinates is None
        assert model.xcoordinates is None
        assert model.ycoordinates is None

    def test_coordinates_given_but_none_expected_throws_value_error(self):
        values = self._create_valid_dummy_model_values()
        values["numcoordinates"] = None

        with pytest.raises(ValidationError):
            TestCoordinatesValidator.DummyModel(**values)

    def test_no_xcoordinates_given_while_expected_throws_value_error(self):
        values = self._create_valid_dummy_model_values()
        values["xcoordinates"] = None

        with pytest.raises(ValidationError):
            TestCoordinatesValidator.DummyModel(**values)

    def test_no_ycoordinates_given_while_expected_throws_value_error(self):
        values = self._create_valid_dummy_model_values()
        values["ycoordinates"] = None

        with pytest.raises(ValidationError):
            TestCoordinatesValidator.DummyModel(**values)

    def test_fewer_xcoordinates_than_expected_throws_value_error(self):
        values = self._create_valid_dummy_model_values()
        values["xcoordinates"] = [1, 2]

        with pytest.raises(ValidationError):
            TestCoordinatesValidator.DummyModel(**values)

    def test_more_xcoordinates_than_expected_throws_value_error(self):
        values = self._create_valid_dummy_model_values()
        values["xcoordinates"] = [1, 2, 3, 4]

        with pytest.raises(ValidationError):
            TestCoordinatesValidator.DummyModel(**values)

    def test_fewer_ycoordinates_than_expected_throws_value_error(self):
        values = self._create_valid_dummy_model_values()
        values["ycoordinates"] = [1, 2]

        with pytest.raises(ValidationError):
            TestCoordinatesValidator.DummyModel(**values)

    def test_more_ycoordinates_than_expected_throws_value_error(self):
        values = self._create_valid_dummy_model_values()
        values["ycoordinates"] = [1, 2, 3, 4]

        with pytest.raises(ValidationError):
            TestCoordinatesValidator.DummyModel(**values)

    def test_fewer_than_minimum_required_number_of_coordinates_throws_value_error(self):
        values = self._create_valid_dummy_model_values()
        values["numcoordinates"] = 1
        values["xcoordinates"] = [1.23]
        values["ycoordinates"] = [9.87]

        with pytest.raises(ValidationError):
            TestCoordinatesValidator.DummyModel(**values)

    def _create_valid_dummy_model_values(self) -> Dict:
        values = dict(
            numcoordinates=3,
            xcoordinates=[1.23, 4.56, 7.89],
            ycoordinates=[9.87, 6.54, 3.21],
        )

        return values
