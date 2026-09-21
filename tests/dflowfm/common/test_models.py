import pytest

from hydrolib.core.dflowfm.common.models import InterpolationMethod


class TestInterpolationMethod:
    @pytest.mark.parametrize(
        "oldmethod, expected",
        [
            (0, InterpolationMethod.linear_space_time),
            (1, InterpolationMethod.linear_space_time),
            (2, InterpolationMethod.linear_space_time),
            (3, InterpolationMethod.linear_space_time),
            (11, InterpolationMethod.linear_space_time),
            (4, InterpolationMethod.constant),
            (5, InterpolationMethod.triangulation),
            (6, InterpolationMethod.averaging),
            (9, InterpolationMethod.averaging),
            (99, "unknown"),
        ],
    )
    def test_from_old_method(self, oldmethod, expected):
        """METHOD=0 maps to linearSpaceTime like 1/2/3/11 (GitHub #1197)."""
        assert InterpolationMethod.from_old_method(oldmethod) == expected
