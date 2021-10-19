import pytest
from typing import List, Optional
from pydantic import ValidationError
from hydrolib.core.io.ini.models import INIBasedModel
from hydrolib.core.io.mdu.models import Lateral


def coordinate_test_cases():
    return [
        pytest.param(None, [42, 24], id="Only y-coord."),
        pytest.param([42, 24], None, id="Only x-coord."),
    ]


class TestModels:
    """Test class to test all classes and methods contained in the
    hydrolib.core.io.mdu.models.py module"""

    class TestLateral:
        """Class to test all methods contained in the
        hydrolib.core.io.mdu.models.Lateral class"""

        @pytest.mark.parametrize("x_coord, y_coord", coordinate_test_cases())
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

        @pytest.mark.parametrize("x_coord, y_coord", coordinate_test_cases())
        def test_given_partial_coordinates_raises(
            self, x_coord: List[int], y_coord: List[int]
        ):
            with pytest.raises(ValidationError) as exc_mssg:
                Lateral(
                    id="42",
                    discharge="A discharge",
                    numCoordinates=2,
                    xCoordinates=x_coord,
                    yCoordinates=y_coord,
                    locationType="loremIpsum",
                )
            expected_error_mssg = (
                "Both xCoordinates and yCoordinates should contain valid values."
            )
            assert expected_error_mssg in str(exc_mssg.value)

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
            "branch_id, chainage",
            [
                pytest.param(None, None, id="Both None."),
                pytest.param(None, "", id="No branchId, empty chainage."),
                pytest.param("", None, id="Empty branchId, no chainage."),
                pytest.param("  ", "  ", id="Both empty."),
                pytest.param("aBranchid", None, id="chainage is None."),
                pytest.param("aBranchid", "  ", id="chainage is empty."),
                pytest.param(None, "achainage", id="BranchId is None."),
                pytest.param("  ", "achainage", id="BranchId is empty."),
            ],
        )
        def test_given_locationType_1d_with_missing_args_raises(
            self, branch_id: str, chainage: str
        ):
            """
            Test to validate how the lateral init fails when no node_id
            is given and the alternative parameters (branchId and chainage)
            are missing or empty.

            Args:
                branch_id (str): Value to assign in the branch field.
                chainage (str): Value to assign in the chainage field.
            """
            with pytest.raises(ValidationError) as exc_mssg:
                Lateral(
                    id="42",
                    discharge="A discharge",
                    numCoordinates=2,
                    xCoordinates=[42, 24],
                    yCoordinates=[24, 42],
                    locationType="1d",
                    branchId=branch_id,
                    chainage=chainage,
                )
            expected_error_mssg = "Field nodeId (or branch_id and chainage) should contain valid values for locationType 1d."
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
            "location_type",
            [pytest.param("1d"), pytest.param("2d"), pytest.param("all")],
        )
        def test_given_valid_args_validates_locationType(self, location_type: str):
            # 1. Define test data.
            x_coords = [42, 24]
            y_coords = [24, 42]
            discharge = "A discharge"
            id_value = "42"
            branch_id = "aBranchId"
            chainage = 4.2

            # 2. Run test.
            lateral_cls = Lateral(
                id=id_value,
                discharge=discharge,
                numCoordinates=2,
                locationType=location_type,
                xCoordinates=x_coords,
                yCoordinates=y_coords,
                branchId=branch_id,
                chainage=chainage,
            )

            # 3. Validate expectations.
            assert isinstance(lateral_cls, INIBasedModel)
            assert lateral_cls.id == id_value
            assert lateral_cls.discharge == discharge
            assert lateral_cls.locationType == location_type
            assert lateral_cls.xCoordinates == x_coords
            assert lateral_cls.yCoordinates == y_coords
            assert lateral_cls.branchId == branch_id
            assert lateral_cls.chainage == chainage
