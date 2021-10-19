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

        def test_given_valid_args_validates_locationType(self):
            lateral_cls = Lateral(
                id="42",
                discharge="A discharge",
                numCoordinates=2,
                locationType="loremIpsum",
                xCoordinates=[42, 24],
                yCoordinates=[24, 42],
            )
            assert isinstance(lateral_cls, INIBasedModel)
