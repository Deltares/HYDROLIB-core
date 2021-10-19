import pytest
from typing import List, Optional
from pydantic import ValidationError
from hydrolib.core.io.mdu.models import Lateral


class TestModels:
    """Test class to test all classes and methods contained in the
    hydrolib.core.io.mdu.models.py module"""

    class TestLateral:
        """Class to test all methods contained in the
        hydrolib.core.io.mdu.models.Lateral class"""

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

        def test_given_coordinates_not_matching_numCoordinates_raises(self):
            pass

        def test_given_partial_coordinates_raises(self):
            with pytest.raises(ValidationError) as exc_mssg:
                Lateral(id="42", numCoordinates=0, xCoordinates=[42], yCoordinates=None)
            assert str(exc_mssg.value)
