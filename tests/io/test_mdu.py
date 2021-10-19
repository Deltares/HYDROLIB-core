from typing import List, Optional

import pytest
from pydantic import ValidationError

from hydrolib.core.io.ini.models import INIBasedModel
from hydrolib.core.io.mdu.models import Lateral


class TestModels:
    """Test class to test all classes and methods contained in the
    hydrolib.core.io.mdu.models.py module"""

    class TestLateral:
        """Class to test all methods contained in the
        hydrolib.core.io.mdu.models.Lateral class"""

        class Test_validate_coordinates:
            """
            Class to test the paradigms for validate_coordinates.
            """

            def test_given_no_numCoordinates_raises_ValueError(self):
                with pytest.raises(ValueError) as exc_mssg:
                    Lateral.validate_coordinates(
                        field_value=[42, 24], values=dict(numCoordinates=None)
                    )
                assert (
                    str(exc_mssg.value)
                    == "numCoordinates should be given when providing x or y coordinates."
                )

            def test_given_wrong_numCoordinates_raises_AssertionError(self):
                with pytest.raises(AssertionError):
                    Lateral.validate_coordinates(
                        field_value=[42, 24], values=dict(numCoordinates=1)
                    )

            def test_given_correct_numCoordinates(self):
                return_value = Lateral.validate_coordinates(
                    field_value=[42, 24], values=dict(numCoordinates=2)
                )
                assert return_value == [42, 24]

        class Test_validate_location_type:
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
            def test_given_wrong_location_type_raises_ValueError(self, value: str):
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
            def test_given_correct_locationType(self, location_type: str):
                return_value = Lateral.validate_location_type(location_type)
                assert return_value == location_type

        class Test_validate_location_dependencies:
            """
            Class to test the paradigms of validate_location_dependencies
            """

            @pytest.mark.parametrize(
                "dict_values",
                [
                    pytest.param(
                        dict(
                            node_id=None, branch_id=None, n_coords=None, chainage=None
                        ),
                        id="All None",
                    ),
                    pytest.param(
                        dict(node_id="", branch_id="", n_coords=0, chainage=None),
                        id="All Empty",
                    ),
                ],
            )
            def test_given_no_values_raises_ValueError(self, dict_values: dict):
                with pytest.raises(ValueError) as exc_err:
                    Lateral.validate_location_dependencies(values=dict_values)
                assert (
                    str(exc_err.value)
                    == "Either nodeId, branchId (with chainage) or numCoordinates (with x, y coordinates) are required."
                )

            @pytest.mark.parametrize(
                "missing_coordinates", [("xCoordinates"), ("yCoordinates")]
            )
            def test_given_numCoords_but_missing_coordinates(
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

            def test_given_numCoordinates_and_valid_coordinates(self):
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

            def test_given_branchId_and_no_chainage_raises_ValueError(self):
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
            @pytest.mark.parametrize(
                "location_type",
                [
                    pytest.param(None, id="None type"),
                    pytest.param("wrongType", id="1d type"),
                ],
            )
            def test_given_1d_args_and_location_type_other_then_raises_ValueError(
                self, dict_values: dict, location_type: str
            ):
                test_values = dict(
                    numCoordinates=2,
                    xCoordinates=[42, 24],
                    yCoordinates=[24, 42],
                    locationType=location_type,
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

        class Test_validate_from_ctor:
            @pytest.mark.parametrize(
                "x_coord, y_coord",
                [
                    pytest.param(None, [42, 24], id="Only y-coord."),
                    pytest.param([42, 24], None, id="Only x-coord."),
                ],
            )
            def test_given_coordinates_but_no_numCoordinates_raises(
                self, x_coord: Optional[List[int]], y_coord: Optional[List[int]]
            ):
                with pytest.raises(ValidationError) as exc_mssg:
                    Lateral(
                        id="42",
                        discharge="A discharge",
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
            def test_given_coordinates_not_matching_numCoordinates_raises(
                self, x_coord: List[int], y_coord: List[int]
            ):
                with pytest.raises(ValidationError):
                    Lateral(
                        id="42",
                        discharge="A discharge",
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
                    discharge="A discharge",
                    numCoordinates=2,
                    xCoordinates=[42, 24],
                    yCoordinates=[24, 42],
                    locationType="all",
                )
                lateral_dict[missing_coord] = None
                with pytest.raises(ValidationError) as exc_mssg:
                    Lateral(**lateral_dict)

                assert f"{missing_coord} should be given." in str(exc_mssg.value)

            def test_given_unknown_locationType_raises(self):
                with pytest.raises(ValidationError) as exc_mssg:
                    location_type = "loremIpsum"
                    Lateral(
                        id="42",
                        discharge="A discharge",
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
                    discharge="A discharge",
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
            def test_given_valid_args_validates_locationType(self, location_dict: str):
                # 1. Define test data.
                default_values = dict(
                    id="42",
                    discharge="A discharge",
                    numCoordinates=2,
                )
                lateral_dict = {**default_values, **location_dict}
                # 2. Run test.
                lateral_cls = Lateral(**lateral_dict)

                # 3. Validate expectations.
                assert isinstance(lateral_cls, INIBasedModel)
                for key, value in lateral_dict.items():
                    assert lateral_cls.dict()[key] == value
