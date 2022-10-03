from typing import Dict, List, Optional

import pytest
from pydantic.error_wrappers import ValidationError

from hydrolib.core.basemodel import BaseModel
from hydrolib.core.io.ini.models import INIBasedModel
from hydrolib.core.io.ini.util import (
    LocationValidationConfiguration,
    LocationValidationFieldNames,
    get_location_specification_rootvalidator,
    get_number_of_coordinates_validator,
)


class TestLocationValidationConfiguration:
    def test_default(self):
        config = LocationValidationConfiguration()
        assert config.validate_node == True
        assert config.validate_coordinates == True
        assert config.validate_branch == True
        assert config.validate_num_coordinates == True
        assert config.minimum_num_coordinates == 0


class TestLocationValidationFieldNames:
    def test_default(self):
        fields = LocationValidationFieldNames()
        assert fields.node_id == "nodeId"
        assert fields.branch_id == "branchId"
        assert fields.chainage == "chainage"
        assert fields.x_coordinates == "xCoordinates"
        assert fields.y_coordinates == "yCoordinates"
        assert fields.num_coordinates == "numCoordinates"
        assert fields.location_type == "locationType"


class TestLocationSpecificationValidator:
    class DummyModel(BaseModel):
        """Dummy model to test the validation of the location specification."""

        nodeid: Optional[str]
        branchid: Optional[str]
        chainage: Optional[str]
        xcoordinates: Optional[List[float]]
        ycoordinates: Optional[List[float]]
        numcoordinates: Optional[int]
        locationtype: Optional[str]

        validator = get_location_specification_rootvalidator(
            config=LocationValidationConfiguration(minimum_num_coordinates=3)
        )

    @pytest.mark.parametrize(
        "values",
        [
            {},
            {
                "nodeid": "some_nodeid",
                "branchid": "some_branchid",
                "chainage": 1.23,
                "xcoordinates": [4.56, 5.67, 6.78],
                "ycoordinates": [7.89, 8.91, 9.12],
                "numcoordinates": 3,
            },
            {
                "xcoordinates": [4.56, 5.67, 6.78],
                "ycoordinates": [7.89, 8.91, 9.12],
            },
            {
                "nodeid": "some_nodeid",
                "branchid": "some_branchid",
                "chainage": 1.23,
            },
            {
                "branchid": "some_branchid",
                "chainage": 1.23,
                "xcoordinates": [4.56, 5.67, 6.78],
            },
            {
                "branchid": "some_branchid",
            },
        ],
    )
    def test_incorrect_fields_provided_raises_error(self, values: dict):
        with pytest.raises(ValidationError) as error:
            TestLocationSpecificationValidator.DummyModel(**values)

        expected_message = "nodeId or branchId and chainage or xCoordinates, yCoordinates and numCoordinates should be provided"
        assert expected_message in str(error.value)

    def test_too_few_coordinates_raises_error(self):
        values = {
            "xcoordinates": [1.23, 2.34],
            "ycoordinates": [3.45, 4.56],
            "numcoordinates": 2,
        }

        with pytest.raises(ValidationError) as error:
            TestLocationSpecificationValidator.DummyModel(**values)

        expected_message = f"numCoordinates should be at least 3"
        assert expected_message in str(error.value)

    def test_coordinate_amount_does_not_match_numcoordinates_raises_error(self):
        values = {
            "xcoordinates": [1.23, 2.34, 3.45],
            "ycoordinates": [4.56, 5.67, 6.78],
            "numcoordinates": 4,
        }

        with pytest.raises(ValidationError) as error:
            TestLocationSpecificationValidator.DummyModel(**values)

        expected_message = "numCoordinates should be equal to the amount of xCoordinates and yCoordinates"
        assert expected_message in str(error.value)

    @pytest.mark.parametrize(
        "values",
        [
            pytest.param(
                {
                    "nodeid": "some_nodeid",
                    "locationtype": "2d",
                },
                id="nodeid",
            ),
            pytest.param(
                {
                    "branchid": "some_branchid",
                    "chainage": 1.23,
                    "locationtype": "2d",
                },
                id="branchid",
            ),
        ],
    )
    def test_incorrect_location_type_raises_error(self, values: dict):
        with pytest.raises(ValidationError) as error:
            TestLocationSpecificationValidator.DummyModel(**values)

        expected_message = "locationType should be 1d but was 2d"
        assert expected_message in str(error.value)

    @pytest.mark.parametrize(
        "values",
        [
            pytest.param(
                {
                    "nodeid": "some_nodeid",
                },
                id="nodeid",
            ),
            pytest.param(
                {
                    "branchid": "some_branchid",
                    "chainage": 1.23,
                },
                id="branchid",
            ),
            pytest.param(
                {
                    "xcoordinates": [4.56, 5.67, 6.78],
                    "ycoordinates": [7.89, 8.91, 9.12],
                    "numcoordinates": 3,
                },
                id="coordinates",
            ),
        ],
    )
    def test_correct_fields_initializes(self, values: dict):
        validated_values = TestLocationSpecificationValidator.DummyModel.validator(
            values
        )
        assert validated_values == values

    @pytest.mark.parametrize(
        "values, expected_values",
        [
            pytest.param(
                {
                    "nodeid": "some_nodeid",
                },
                {"nodeid": "some_nodeid", "locationtype": "1d"},
                id="nodeid",
            ),
            pytest.param(
                {"branchid": "some_branchid", "chainage": 1.23},
                {"branchid": "some_branchid", "chainage": 1.23, "locationtype": "1d"},
                id="branchid",
            ),
        ],
    )
    def test_correct_1d_fields_locationtype_is_added(
        self, values: dict, expected_values: dict
    ):
        validated_values = TestLocationSpecificationValidator.DummyModel.validator(
            values
        )
        assert validated_values == expected_values


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
