from typing import List, Optional

import pytest
from pathlib import Path
from pydantic import ValidationError

from hydrolib.core.io.ini.models import INIBasedModel
from hydrolib.core.io.bc.models import ForcingModel
from hydrolib.core.io.mdu.models import Boundary, Lateral


class TestModels:
    """Test class to test all classes and methods contained in the
    hydrolib.core.io.mdu.models.py module"""

    class TestLateral:
        """Class to test all methods contained in the
        hydrolib.core.io.mdu.models.Lateral class"""

        class TestValidateCoordinates:
            """
            Class to test the paradigms for validate_coordinates.
            """

            def test_given_no_numcoordinates_raises_valueerror(self):
                with pytest.raises(ValueError) as exc_mssg:
                    Lateral.validate_coordinates(
                        field_value=[42, 24], values=dict(numCoordinates=None)
                    )
                assert (
                    str(exc_mssg.value)
                    == "numCoordinates should be given when providing x or y coordinates."
                )

            def test_given_wrong_numcoordinates_raises_assertionerror(self):
                with pytest.raises(AssertionError) as exc_mssg:
                    Lateral.validate_coordinates(
                        field_value=[42, 24], values=dict(numCoordinates=1)
                    )
                assert (
                    str(exc_mssg.value)
                    == "Number of coordinates given (2) not matching the numCoordinates value 1."
                )

            def test_given_correct_numcoordinates(self):
                return_value = Lateral.validate_coordinates(
                    field_value=[42, 24], values=dict(numCoordinates=2)
                )
                assert return_value == [42, 24]

        class TestValidateLocationType:
            """
            Class to test the paradigms for validate_location_type
            """

            @pytest.mark.parametrize(
                "value",
                [
                    pytest.param(""),
                    pytest.param("  "),
                    pytest.param("notAValidType"),
                ],
            )
            def test_given_wrong_location_type_raises_valueerror(self, value: str):
                with pytest.raises(ValueError) as exc_mssg:
                    Lateral.validate_location_type(value)
                assert (
                    str(exc_mssg.value)
                    == f"Value given ({value}) not accepted, should be one of: 1d, 2d, all"
                )

            @pytest.mark.parametrize(
                "location_type",
                [
                    pytest.param("1d"),
                    pytest.param("1D"),
                    pytest.param("2d"),
                    pytest.param("2D"),
                    pytest.param("all"),
                    pytest.param("All"),
                    pytest.param("ALL"),
                ],
            )
            def test_given_correct_locationtype(self, location_type: str):
                return_value = Lateral.validate_location_type(location_type)
                assert return_value == location_type

        class TestValidateLocationTypeDependencies:
            """
            Class to test the paradigms of validate_location_dependencies
            """

            @pytest.mark.parametrize(
                "dict_values",
                [
                    pytest.param(
                        dict(nodeId=None, branch_id=None, n_coords=None, chainage=None),
                        id="All None",
                    ),
                    pytest.param(
                        dict(nodeId="", branch_id="", n_coords=0, chainage=None),
                        id="All Empty",
                    ),
                ],
            )
            def test_given_no_values_raises_valueerror(self, dict_values: dict):
                with pytest.raises(ValueError) as exc_err:
                    Lateral.validate_location_dependencies(values=dict_values)
                assert (
                    str(exc_err.value)
                    == "Either nodeId, branchId (with chainage) or numCoordinates (with x, y coordinates) are required."
                )

            @pytest.mark.parametrize(
                "missing_coordinates", [("xCoordinates"), ("yCoordinates")]
            )
            def test_given_numcoords_but_missing_coordinates(
                self, missing_coordinates: str
            ):
                test_dict = dict(
                    nodeId=None,
                    branchId=None,
                    chainage=None,
                    numCoordinates=2,
                    xCoordinates=[42, 24],
                    yCoordinates=[24, 42],
                )
                test_dict[missing_coordinates] = None
                with pytest.raises(ValueError) as exc_error:
                    Lateral.validate_location_dependencies(test_dict)
                assert str(exc_error.value) == f"{missing_coordinates} should be given."

            def test_given_numcoordinates_and_valid_coordinates(self):
                test_dict = dict(
                    nodeId=None,
                    branchId=None,
                    chainage=None,
                    numCoordinates=2,
                    xCoordinates=[42, 24],
                    yCoordinates=[24, 42],
                )
                return_value = Lateral.validate_location_dependencies(test_dict)
                assert return_value == test_dict

            def test_given_branchid_and_no_chainage_raises_valueerror(self):
                with pytest.raises(ValueError) as exc_err:
                    Lateral.validate_location_dependencies(
                        dict(
                            nodeId=None,
                            branchId="aBranchId",
                            chainage=None,
                        )
                    )
                assert (
                    str(exc_err.value)
                    == "Chainage should be provided when branchId specified."
                )

            @pytest.mark.parametrize(
                "dict_values",
                [
                    pytest.param(dict(nodeId="42"), id="Given nodeId"),
                    pytest.param(
                        dict(branchId="aBranchId", chainage=4.2),
                        id="Given branchId and chainage",
                    ),
                ],
            )
            def test_given_1d_args_and_location_type_other_then_raises_valueerror(
                self, dict_values: dict
            ):
                test_values = dict(
                    numCoordinates=2,
                    xCoordinates=[42, 24],
                    yCoordinates=[24, 42],
                    locationType="wrongType",
                )
                test_dict = {**dict_values, **test_values}
                with pytest.raises(ValueError) as exc_err:
                    Lateral.validate_location_dependencies(test_dict)
                assert (
                    str(exc_err.value)
                    == "LocationType should be 1d when nodeId (or branchId and chainage) specified."
                )

            @pytest.mark.parametrize(
                "dict_values",
                [
                    pytest.param(dict(nodeId="24"), id="Given nodeId"),
                    pytest.param(
                        dict(branchId="aBranchId", chainage=4.2),
                        id="Given branchId and chainage.",
                    ),
                ],
            )
            def test_given_1d_args_and_1d_location_type(self, dict_values: dict):
                test_values = dict(
                    numCoordinates=2,
                    xCoordinates=[42, 24],
                    yCoordinates=[24, 42],
                    locationType="1d",
                )
                test_dict = {**dict_values, **test_values}
                return_value = Lateral.validate_location_dependencies(test_dict)
                assert return_value == test_dict

            @pytest.mark.parametrize(
                "test_dict",
                [
                    pytest.param(dict(nodeId="aNodeId"), id="With NodeId"),
                    pytest.param(
                        dict(branchId="aBranchId", chainage=42),
                        id="Witch branchId and chainage",
                    ),
                ],
            )
            @pytest.mark.parametrize(
                "location_type",
                [
                    pytest.param("", id="Empty string"),
                    pytest.param(None, id="None string"),
                ],
            )
            def test_given_1d_args_but_no_locationtype_then_sets_value(
                self, test_dict: dict, location_type: str
            ):
                test_dict["locationType"] = location_type
                return_value = Lateral.validate_location_dependencies(test_dict)
                assert return_value["locationType"] == "1d"

        class TestValidateFromCtor:
            @pytest.mark.parametrize(
                "x_coord, y_coord",
                [
                    pytest.param(None, [42, 24], id="Only y-coord."),
                    pytest.param([42, 24], None, id="Only x-coord."),
                ],
            )
            def test_given_coordinates_but_no_numcoordinates_raises(
                self, x_coord: Optional[List[int]], y_coord: Optional[List[int]]
            ):
                with pytest.raises(ValidationError) as exc_mssg:
                    Lateral(
                        id="42",
                        discharge="aDischarge",
                        numCoordinates=None,
                        xCoordinates=x_coord,
                        yCoordinates=y_coord,
                    )

                expected_error_mssg = (
                    "numCoordinates should be given when providing x or y coordinates."
                )
                assert expected_error_mssg in str(exc_mssg.value)

            @pytest.mark.parametrize(
                "x_coord, y_coord",
                [
                    pytest.param([42, 24], [24], id="Y coord not matching."),
                    pytest.param([24], [42, 24], id="X coord not matching."),
                ],
            )
            def test_given_coordinates_not_matching_numcoordinates_raises(
                self, x_coord: List[int], y_coord: List[int]
            ):
                with pytest.raises(ValidationError):
                    Lateral(
                        id="42",
                        discharge="bDischarge",
                        numCoordinates=2,
                        xCoordinates=x_coord,
                        yCoordinates=y_coord,
                    )

            @pytest.mark.parametrize(
                "missing_coord", [("xCoordinates"), ("yCoordinates")]
            )
            def test_given_partial_coordinates_raises(self, missing_coord: str):
                lateral_dict = dict(
                    id="42",
                    discharge="cDischarge",
                    numCoordinates=2,
                    xCoordinates=[42, 24],
                    yCoordinates=[24, 42],
                    locationType="all",
                )
                lateral_dict[missing_coord] = None
                with pytest.raises(ValidationError) as exc_mssg:
                    Lateral(**lateral_dict)

                assert f"{missing_coord} should be given." in str(exc_mssg.value)

            def test_given_unknown_locationtype_raises(self):
                with pytest.raises(ValidationError) as exc_mssg:
                    location_type = "loremIpsum"
                    Lateral(
                        id="42",
                        discharge="dDischarge",
                        numCoordinates=2,
                        xCoordinates=[42, 24],
                        yCoordinates=[24, 42],
                        locationType=location_type,
                    )
                expected_error_mssg = f"Value given ({location_type}) not accepted, should be one of: 1d, 2d, all"
                assert expected_error_mssg in str(exc_mssg.value)

            @pytest.mark.parametrize(
                "location_values",
                [
                    pytest.param(dict(nodeId="aNodeId"), id="nodeId given."),
                    pytest.param(
                        dict(branchId="aBranchId", chainage=42),
                        id="branchId + chainage given.",
                    ),
                    pytest.param(
                        dict(nodeId="aNodeId", branchId="aBranchId", chainage=42),
                        id="all given.",
                    ),
                    pytest.param(
                        dict(nodeId="", branchId="aBranchId", chainage=42),
                        id="Empty nodeId.",
                    ),
                ],
            )
            def test_given_valid_location_args_constructs_lateral(
                self, location_values: dict
            ):
                # 1. Define test data.
                default_values = dict(
                    id="42",
                    discharge="eDischarge",
                    numCoordinates=2,
                    xCoordinates=[42, 24],
                    yCoordinates=[24, 42],
                    locationType="1d",
                )
                test_dict = {**default_values, **location_values}

                # 2. Run test.
                new_lateral = Lateral(**test_dict)

                # 3. Validate final expectations.
                for key, value in location_values.items():
                    assert new_lateral.dict()[key] == value

            @pytest.mark.parametrize(
                "location_dict",
                [
                    pytest.param(
                        dict(locationType="1d", nodeId="aNodeId"), id="1D-With NodeId"
                    ),
                    pytest.param(
                        dict(locationType="1d", branchId="aBranchId", chainage=4.2),
                        id="1D-With BranchId and Chainage",
                    ),
                    pytest.param(
                        dict(
                            locationType="2d",
                            xCoordinates=[42, 24],
                            yCoordinates=[24, 42],
                        ),
                        id="2D-With coordinates",
                    ),
                    pytest.param(
                        dict(
                            locationType="all",
                            xCoordinates=[42, 24],
                            yCoordinates=[24, 42],
                        ),
                        id="All-With coordinates",
                    ),
                ],
            )
            def test_given_valid_args_validates_locationtype(self, location_dict: str):
                # 1. Define test data.
                default_values = dict(
                    id="42",
                    discharge="fDischarge",
                    numCoordinates=2,
                )
                lateral_dict = {**default_values, **location_dict}
                # 2. Run test.
                lateral_cls = Lateral(**lateral_dict)

                # 3. Validate expectations.
                assert isinstance(lateral_cls, INIBasedModel)
                for key, value in lateral_dict.items():
                    assert lateral_cls.dict()[key] == value

    class TestBoundary:
        """Class to test all methods contained in the
        hydrolib.core.io.mdu.models.Boundary class"""

        def test_given_args_expected_values(self):
            # 1. Explicit declaration of parameters (to validate keys as they are written)
            dict_values = {
                "quantity": "42",
                "nodeid": "aNodeId",
                "locationfile": Path("aLocationFile"),
                "forcingfile": ForcingModel(),
                "bndwidth1d": 4.2,
            }

            # 2. Create boundary.
            created_boundary = Boundary(**dict_values)

            # 3. Verify boundary values as expected.
            for key, value in dict_values.items():
                assert created_boundary.dict()[key] == value

        def test_given_args_as_alias_expected_values(self):
            # 1. Explicit declaration of parameters (to validate keys as they are written)
            dict_values = {
                "quantity": "42",
                "nodeId": "aNodeId",
                "locationFile": Path("aLocationFile"),
                "forcingFile": ForcingModel(),
                "bndWidth1d": 4.2,
            }

            # 2. Create boundary.
            created_boundary = Boundary(**dict_values)
            boundary_as_dict = created_boundary.dict()
            # 3. Verify boundary values as expected.
            assert boundary_as_dict["quantity"] == dict_values["quantity"]
            assert boundary_as_dict["nodeid"] == dict_values["nodeId"]
            assert boundary_as_dict["locationfile"] == dict_values["locationFile"]
            assert boundary_as_dict["forcingfile"] == dict_values["forcingFile"]
            assert boundary_as_dict["bndwidth1d"] == dict_values["bndWidth1d"]

        class TestValidateRootValidator:
            """
            Test class to validate the paradigms when evaluating
            check_nodeid_or_locationfile_present.
            """

            @pytest.mark.parametrize(
                "dict_values",
                [
                    pytest.param(dict(), id="No entries."),
                    pytest.param(
                        dict(nodeid=None, locationfile=None), id="Entries are None."
                    ),
                    pytest.param(
                        dict(nodeid="", locationfile=""), id="Entries are Empty."
                    ),
                ],
            )
            def test_given_no_values_raises_valueerror(self, dict_values: dict):
                with pytest.raises(ValueError) as exc_mssg:
                    Boundary.check_nodeid_or_locationfile_present(dict_values)

                # 3. Verify final expectations.
                expected_error_mssg = (
                    "Either nodeId or locationFile fields should be specified."
                )
                assert str(exc_mssg.value) == expected_error_mssg

            @pytest.mark.parametrize(
                "dict_values",
                [
                    pytest.param(dict(nodeid="aNodeId"), id="NodeId present."),
                    pytest.param(
                        dict(locationfile=Path("aLocationFile")),
                        id="LocationFile present.",
                    ),
                    pytest.param(
                        dict(nodeid="bNodeId", locationfile="bLocationFile"),
                        id="Both present.",
                    ),
                ],
            )
            def test_given_dict_values_doesnot_raise(self, dict_values: dict):
                return_values = Boundary.check_nodeid_or_locationfile_present(
                    dict_values
                )
                assert dict_values == return_values

        class TestValidateFromCtor:
            @pytest.mark.parametrize(
                "dict_values",
                [
                    pytest.param(dict(), id="No entries."),
                    pytest.param(
                        dict(nodeid=None, locationfile=None), id="Entries are None."
                    ),
                    pytest.param(dict(nodeid=""), id="NodeId is empty."),
                ],
            )
            def test_given_no_values_raises_valueerror(self, dict_values: dict):
                required_values = dict(quantity="aQuantity")
                test_values = {**dict_values, **required_values}
                with pytest.raises(ValueError) as exc_mssg:
                    Boundary(**test_values)

                # 3. Verify final expectations.
                expected_error_mssg = (
                    "Either nodeId or locationFile fields should be specified."
                )
                assert expected_error_mssg in str(exc_mssg.value)

            @pytest.mark.parametrize(
                "dict_values",
                [
                    pytest.param(dict(nodeid="aNodeId"), id="NodeId present."),
                    pytest.param(
                        dict(locationfile=Path("aLocationFile")),
                        id="LocationFile present.",
                    ),
                    pytest.param(
                        dict(nodeid="bNodeId", locationfile=Path("bLocationFile")),
                        id="Both present.",
                    ),
                ],
            )
            def test_given_dict_values_doesnot_raise(self, dict_values: dict):
                required_values = dict(quantity="aQuantity", forcingfile=ForcingModel())
                test_values = {**dict_values, **required_values}
                created_boundary = Boundary(**test_values)
                for key, value in test_values.items():
                    if key == "forcing_file":
                        value = value.dict()
                    assert created_boundary.dict()[key] == value
