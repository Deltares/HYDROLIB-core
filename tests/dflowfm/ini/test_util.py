from typing import Dict, List, Literal, Optional
from unittest.mock import Mock

import pytest
from pydantic import ValidationError, field_validator, model_validator
from pydantic.fields import FieldInfo

from hydrolib.core.base.models import BaseModel
from hydrolib.core.dflowfm.ini.util import (
    LocationValidationConfiguration,
    LocationValidationFieldNames,
    UnknownKeywordErrorManager,
    get_from_subclass_defaults,
    rename_keys_for_backwards_compatibility,
    validate_datetime_string,
    validate_location_specification,
)


class TestLocationValidationConfiguration:
    def test_default(self):
        config = LocationValidationConfiguration()
        assert config.validate_node == True
        assert config.validate_coordinates == True
        assert config.validate_branch == True
        assert config.validate_num_coordinates == True
        assert config.validate_location_type == True
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

        @model_validator(mode="before")
        def validate_that_location_specification_is_correct(cls, values: Dict) -> Dict:
            return validate_location_specification(
                values,
                config=LocationValidationConfiguration(minimum_num_coordinates=3),
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

        expected_message = (
            "xCoordinates and yCoordinates should have at least 3 coordinate(s)"
        )
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
        validated_values = validate_location_specification(
            values,
            config=LocationValidationConfiguration(minimum_num_coordinates=3),
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
        validated_values = validate_location_specification(
            values,
            config=LocationValidationConfiguration(minimum_num_coordinates=3),
        )
        assert validated_values == expected_values

    @pytest.mark.parametrize(
        "values",
        [
            pytest.param({"nodeid": "some_nodeid"}, id="nodeId"),
            pytest.param(
                {"branchid": "some_branchid", "chainage": 123},
                id="branch specification",
            ),
        ],
    )
    def test_validate_location_type_false_does_not_add_location_type(
        self, values: dict
    ):
        config = LocationValidationConfiguration(validate_location_type=False)
        validated_values = validate_location_specification(values, config)

        assert validated_values == values

    @pytest.mark.parametrize(
        "values",
        [
            pytest.param({"nodeid": "some_nodeid"}, id="nodeId"),
            pytest.param(
                {"branchid": "some_branchid", "chainage": 123},
                id="branch specification",
            ),
        ],
    )
    def test_validate_location_type_false_does_not_validate_location_type(
        self, values: dict
    ):
        config = LocationValidationConfiguration(validate_location_type=False)
        values["locationtype"] = "This is an invalid location type..."

        validated_values = validate_location_specification(values, config)

        assert validated_values == values


class TestGetKeyRenamingRootValidator:
    class DummyModel(BaseModel):
        """Dummy model to test the validation of the location specification."""

        randomproperty: str

        @model_validator(mode="before")
        @classmethod
        def rename_keys(cls, values):
            if isinstance(values, dict):
                return rename_keys_for_backwards_compatibility(
                    values,
                    {
                        "randomproperty": [
                            "randomProperty",
                            "random_property",
                            "oldRandomProperty",
                        ],
                    },
                )
            return values

        model_config = {"extra": "allow", "populate_by_name": True}

    @pytest.mark.parametrize(
        "old_key", ["randomProperty", "random_property", "oldRandomProperty"]
    )
    def test_old_keys_are_correctly_renamed_to_current_keyword(self, old_key: str):
        values = {old_key: "randomString"}

        model = TestGetKeyRenamingRootValidator.DummyModel(**values)

        assert model.randomproperty == "randomString"

    def test_unknown_key_still_raises_error(self):
        values = {"randomKeyThatNeverExisted": "randomString"}

        with pytest.raises(ValidationError) as error:
            TestGetKeyRenamingRootValidator.DummyModel(**values)

        expected_message = "Field required"
        assert expected_message in str(error.value)


class TestGetFromSubclassDefaults:
    def test_get_from_subclass_defaults__correctly_gets_default_property_from_child(
        self,
    ):
        name = get_from_subclass_defaults(
            BaseClass,
            "name",
            "WithDefaultProperty",
        )

        assert name == "WithDefaultProperty"

    def test_get_from_subclass_defaults__correctly_gets_default_property_from_grandchild(
        self,
    ):
        name = get_from_subclass_defaults(
            BaseClass,
            "name",
            "GrandChildWithDefaultProperty",
        )

        assert name == "GrandChildWithDefaultProperty"

    def test_get_from_subclass_defaults__returns_value_if_no_corresponding_defaults_found(
        self,
    ):
        name = get_from_subclass_defaults(
            BaseClass,
            "name",
            "ThisDefaultValueDoesNotExist",
        )

        assert name == "ThisDefaultValueDoesNotExist"

    def test_get_from_subclass_defaults__property_not_found__returns_value(self):
        value = "valueToCheck"

        default = get_from_subclass_defaults(
            BaseClass,
            "unknownProperty",
            value,
        )

        assert default == value


class BaseClass(BaseModel):
    name: str


class WithDefaultProperty(BaseClass):
    name: Literal["WithDefaultProperty"] = "WithDefaultProperty"
    model_config = {"populate_by_name": True}


class WithoutDefaultProperty(BaseClass):
    pass


class GrandChildWithDefaultProperty(WithoutDefaultProperty):
    name: Literal["GrandChildWithDefaultProperty"] = "GrandChildWithDefaultProperty"
    model_config = {"populate_by_name": True}


class TestUnknownKeywordErrorManager:
    def test_unknown_keywords_given_when_notify_unknown_keywords_gives_error_with_unknown_keywords(
        self,
    ):
        section_header = "section header"
        fields = {}
        excluded_fields = set()
        name = "keyname"
        second_name = "second_other"

        ukem = UnknownKeywordErrorManager()
        data = {name: 1, second_name: 2}

        expected_message = f"Unknown keywords are detected in section: '{section_header}', '{[name, second_name]}'"

        with pytest.raises(ValueError) as exc_err:
            ukem.raise_error_for_unknown_keywords(
                data, section_header, fields, excluded_fields
            )

        assert expected_message in str(exc_err.value)

    def test_keyword_given_known_as_alias_does_not_throw_exception(self):
        section_header = "section header"
        excluded_fields = set()
        name = "keyname"

        mocked_field = Mock(spec=FieldInfo)
        mocked_field.name = "name"
        mocked_field.alias = name

        fields = {"name": mocked_field}

        ukem = UnknownKeywordErrorManager()
        data = {name: 1}

        try:
            ukem.raise_error_for_unknown_keywords(
                data, section_header, fields, excluded_fields
            )
        except ValueError:
            pytest.fail("Exception is thrown, no exception is expected for this test.")

    def test_keyword_given_known_as_name_does_not_throw_exception(self):
        section_header = "section header"
        excluded_fields = set()
        name = "keyname"

        mocked_field = Mock(spec=FieldInfo)
        mocked_field.name = "name"
        mocked_field.alias = name

        fields = {name: mocked_field}

        ukem = UnknownKeywordErrorManager()
        data = {name: 1}

        try:
            ukem.raise_error_for_unknown_keywords(
                data, section_header, fields, excluded_fields
            )
        except ValueError:
            pytest.fail("Exception is thrown, no exception is expected for this test.")

    def test_keyword_given_known_as_excluded_field_does_not_throw_exception(self):
        section_header = "section header"
        excluded_fields = set()
        name = "keyname"
        excluded_fields.add(name)

        fields = {}

        ukem = UnknownKeywordErrorManager()
        data = {name: 1}

        try:
            ukem.raise_error_for_unknown_keywords(
                data, section_header, fields, excluded_fields
            )
        except ValueError:
            pytest.fail("Exception is thrown, no exception is expected for this test.")


class TestDateTimeValidator:
    @pytest.mark.parametrize(
        "date_value",
        [
            ("20230101"),
            ("20231231"),
            ("20230101000000"),
            ("20231231235959"),
        ],
        ids=[
            "Date start of year",
            "Date end of year",
            "DateTime start of year",
            "DateTime end of year",
        ],
    )
    def test_mdu_datetime_valid_format_returns_value(self, date_value):
        field = Mock(spec=ModelField)
        field.name = "timefield"
        field.alias = "timeField"

        returned_value = validate_datetime_string(date_value, field)

        assert returned_value == date_value

    @pytest.mark.parametrize(
        "date_value",
        [
            ("invalid"),
            ("2023010"),
            ("202312311"),
            ("2023010100000"),
            ("202301010000000"),
        ],
        ids=[
            "unknown format",
            "Date too short",
            "Date too long",
            "DateTime too short",
            "DateTime too long",
        ],
    )
    def test_mdu_datetime_invalid_format_raises_valueerror(self, date_value):
        field = Mock(spec=ModelField)
        field.name = "timefield"
        field.alias = "timeField"

        with pytest.raises(ValueError) as exc_err:
            validate_datetime_string(date_value, field)

        assert (
            f"Invalid datetime string for {field.alias}: '{date_value}', expecting 'YYYYmmddHHMMSS' or 'YYYYmmdd'."
            in str(exc_err.value)
        )
