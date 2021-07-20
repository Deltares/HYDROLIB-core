from hydrolib.io.polyfile import Parser, Point
from typing import Optional, Tuple

import pytest


class TestParser:
    @pytest.mark.parametrize(
        "input,expected_value",
        [
            ("* some comment", True),
            ("*", True),
            ("*         ", True),
            ("", False),
            ("potato", False),
            ("1_1", False),
            ("1_1:type=terrainjump", False),
            ("Not a comment but a regular string", False),
            ("      ", False),
            ("         * some comment", False),
        ],
    )
    def test_is_comment(self, input: str, expected_value: bool):
        assert Parser._is_comment(input) == expected_value

    @pytest.mark.parametrize(
        "input,expected_value",
        [
            ("* some comment", " some comment"),
            ("*", ""),
            ("*   ", ""),
        ],
    )
    def test_convert_to_comment(self, input: str, expected_value: str):
        assert Parser._convert_to_comment(input) == expected_value

    @pytest.mark.parametrize(
        "input,expected_value",
        [
            ("potato", True),
            ("1_1", True),
            ("1_1:type=terrainjump", True),
            ("* some comment", False),
            ("*", False),
            ("*         ", False),
            ("", False),
            ("Not a comment but a regular string", False),
            ("      ", False),
        ],
    )
    def test_is_name(self, input: str, expected_value: bool):
        assert Parser._is_name(input) == expected_value

    @pytest.mark.parametrize(
        "input,expected_value",
        [
            ("potato", "potato"),
            ("    potato     ", "potato"),
            ("1_1  ", "1_1"),
            ("1_1:type=terrainjump", "1_1:type=terrainjump"),
        ],
    )
    def test_convert_to_name(self, input: str, expected_value: str):
        assert Parser._convert_to_name(input) == expected_value

    @pytest.mark.parametrize(
        "input,expected_value",
        [
            ("1 1", (1, 1)),
            ("   201     88    ", (201, 88)),
            ("0 1", None),
            ("201 0", None),
            ("0 0", None),
            ("-5 20", None),
            ("-5 -20", None),
            ("5 -20", None),
            ("1 1.0", None),
            ("1.0 1", None),
            ("1.0 1.0", None),
        ],
    )
    def test_convert_to_dimensions(
        self, input: str, expected_value: Optional[Tuple[int, int]]
    ):
        assert Parser._convert_to_dimensions(input) == expected_value

    @pytest.mark.parametrize(
        "input,n_total_points,has_z,expected_value",
        [
            ("1.0  2.0", 2, False, Point(x=1.0, y=2.0, z=None, data=[])),
            ("1.0  2.0  3.0", 3, True, Point(x=1.0, y=2.0, z=3.0, data=[])),
            (
                "1.0  2.0  3.0",
                3,
                False,
                Point(
                    x=1.0,
                    y=2.0,
                    z=None,
                    data=[
                        3.0,
                    ],
                ),
            ),
            (
                "1.0  2.0  3.0  4.0  5.0",
                5,
                True,
                Point(
                    x=1.0,
                    y=2.0,
                    z=3.0,
                    data=[
                        4.0,
                        5.0,
                    ],
                ),
            ),
            (
                "    1.0    2.0    3.0    4.0    5.0        ",
                5,
                True,
                Point(
                    x=1.0,
                    y=2.0,
                    z=3.0,
                    data=[
                        4.0,
                        5.0,
                    ],
                ),
            ),
            (
                "    1    2    3    4    5        ",
                5,
                True,
                Point(
                    x=1.0,
                    y=2.0,
                    z=3.0,
                    data=[
                        4.0,
                        5.0,
                    ],
                ),
            ),
            ("    a    2    3    4    5        ", 5, True, None),
            ("    1.0    2.0    3.0    4.0    5.0        ", 3, True, None),
            ("    1.0    2.0    3.0    4.0    5.0        ", 6, True, None),
            ("1.0,  2.0,", 2, False, None),
            ("1.a  2.b", 2, False, None),
            ("-1.0  -2.0", 2, False, Point(x=-1.0, y=-2.0, z=None, data=[])),
        ],
    )
    def test_convert_to_point(
        self, input: str, n_total_points: int, has_z: bool, expected_value: Point
    ):
        assert Parser._convert_to_point(input, n_total_points, has_z) == expected_value
