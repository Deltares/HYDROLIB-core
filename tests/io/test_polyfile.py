from hydrolib.io.common import ParseMsg
from hydrolib.io.polyfile import (
    Block,
    Description,
    ErrorBuilder,
    InvalidBlock,
    Parser,
    Point,
    PolyObject,
    Metadata,
    _determine_has_z_value,
)
from pathlib import Path
from typing import Iterator, List, Optional, Tuple, Union

import pytest


class TestDescription:
    @pytest.mark.parametrize(
        "description,expected_output",
        [
            (Description(content=""), "*"),
            (Description(content="    "), "*"),
            (Description(content="some comment"), "*some comment"),
            (Description(content=" some comment"), "* some comment"),
            (Description(content=" multiple\n lines"), "* multiple\n* lines"),
            (
                Description(content=" multiple lines\n\n\n with whitespace"),
                "* multiple lines\n*\n*\n* with whitespace",
            ),
        ],
    )
    def test_serialise(self, description: Description, expected_output: str):
        assert description.serialise() == expected_output


class TestMetadata:
    @pytest.mark.parametrize(
        "metadata,expected_output",
        [
            (Metadata(name="some-name", n_rows=5, n_columns=10), "some-name\n5    10"),
            (Metadata(name="name", n_rows=25, n_columns=10), "name\n25    10"),
        ],
    )
    def test_serialise(self, metadata: Metadata, expected_output: str):
        assert metadata.serialise() == expected_output


class TestPoint:
    @pytest.mark.parametrize(
        "point,expected_output",
        [
            (
                Point(
                    x=0.0,
                    y=1.0,
                    z=2.0,
                    data=[
                        3.0,
                        4.0,
                        5.0,
                    ],
                ),
                "    0.0    1.0    2.0    3.0    4.0    5.0",
            ),
            (
                Point(
                    x=0.0,
                    y=1.0,
                    z=None,
                    data=[
                        2.0,
                        3.0,
                        4.0,
                        5.0,
                    ],
                ),
                "    0.0    1.0    2.0    3.0    4.0    5.0",
            ),
            (
                Point(
                    x=0.0,
                    y=1.0,
                    z=None,
                    data=[],
                ),
                "    0.0    1.0",
            ),
        ],
    )
    def test_serialise(self, point: Point, expected_output: str):
        assert point.serialise() == expected_output


class TestBlock:
    def test_finalise_valid_state_returns_corresponding_poly_object(self):
        warning_msgs = [ParseMsg(line=(0, 0), column=None, reason="")]

        block = Block(
            start_line=0,
            description=None,
            name="some-name",
            dimensions=(4, 5),
            points=[],
            ws_warnings=warning_msgs,
        )

        expected_object = PolyObject(
            description=None,
            metadata=Metadata(name="some-name", n_rows=4, n_columns=5),
            points=[],
        )

        (result_object, result_warnings) = block.finalise()  # type: ignore
        assert result_warnings == warning_msgs
        assert result_object == expected_object

    @pytest.mark.parametrize(
        "name,dimensions,points",
        [
            (None, (1, 1), []),
            ("name", None, []),
            ("name", (1, 1), None),
            (None, None, None),
        ],
    )
    def test_finalise_invalid_state_returns_none(
        self,
        name: Optional[str],
        dimensions: Optional[Tuple[int, int]],
        points: Optional[List[Point]],
    ):
        block = Block(start_line=0, name=name, dimensions=dimensions, points=points)
        assert block.finalise() is None


class TestPolyObject:
    def test_serialise(self):
        poly_object = PolyObject(
            description=Description(content=" description\n more description"),
            metadata=Metadata(name="name", n_rows=2, n_columns=2),
            points=[
                Point(x=1.0, y=2.0, z=None, data=[]),
                Point(x=3.0, y=4.0, z=None, data=[]),
            ],
        )

        expected_str = """* description
* more description
name
2    2
    1.0    2.0
    3.0    4.0"""

        assert poly_object.serialise() == expected_str


class TestInvalidBlock:
    def to_msg_returns_corresponding_msg(self):
        block = InvalidBlock(
            start_line=0, end_line=20, invalid_line=10, reason="reason"
        )
        expected_msg = ParseMsg(line=(0, 20), reason="reason at line 10")
        assert block.to_msg() == expected_msg


class TestErrorBuilder:
    def test_finalise_previous_error_no_error_returns_none(self):
        builder = ErrorBuilder()
        assert builder.finalise_previous_error() is None

    def test_finalise_previous_error(self):
        builder = ErrorBuilder()

        line = (0, 20)
        invalid_line = 10
        reason = "reason"
        expected_reason = f"reason at line {invalid_line}."

        builder.start_invalid_block(line[0], invalid_line, reason)
        builder.end_invalid_block(line[1])
        msg = builder.finalise_previous_error()

        assert msg is not None
        assert msg.line == line
        assert msg.reason == expected_reason

    def test_finalise_previous_error_after_adding_second_start(self):
        builder = ErrorBuilder()

        line = (0, 20)
        invalid_line = 10
        reason = "reason"
        expected_reason = f"reason at line {invalid_line}."

        builder.start_invalid_block(line[0], invalid_line, reason)
        builder.start_invalid_block(12, 15, "some other reason")
        builder.end_invalid_block(line[1])
        msg = builder.finalise_previous_error()

        assert msg is not None
        assert msg.line == line
        assert msg.reason == expected_reason


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
            ("         * some comment", True),
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
            ("1", None),
            ("a", None),
            ("* Description", None),
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

    def test_correct_pli_expected_result(self):
        input_data = """* Some header
* with multiple
* descriptions
the-name
2    3
1.0 2.0 3.0
4.0 5.0 6.0
another-name
3    2
7.0 8.0
9.0 10.0
11.0 12.0"""

        expected_poly_objects = [
            PolyObject(
                description=Description(
                    content=" Some header\n with multiple\n descriptions"
                ),
                metadata=Metadata(name="the-name", n_rows=2, n_columns=3),
                points=[
                    Point(x=1.0, y=2.0, z=None, data=[3.0]),
                    Point(x=4.0, y=5.0, z=None, data=[6.0]),
                ],
            ),
            PolyObject(
                description=None,
                metadata=Metadata(name="another-name", n_rows=3, n_columns=2),
                points=[
                    Point(x=7.0, y=8.0, z=None, data=[]),
                    Point(x=9.0, y=10.0, z=None, data=[]),
                    Point(x=11.0, y=12.0, z=None, data=[]),
                ],
            ),
        ]

        parser = Parser(has_z_value=False)

        for l in input_data.splitlines():
            parser.feed_line(l)

        (poly_objects, errors, warnings) = parser.finalise()

        assert len(errors) == 0
        assert len(warnings) == 0

        assert poly_objects == expected_poly_objects

    @pytest.mark.parametrize(
        "input,warnings_description",
        [
            (
                """*description
name
1 2
0.0 0.0""",
                [],
            ),
            (
                """    * description
name
1 2
0.0 0.0""",
                [(0, 3)],
            ),
            (
                """* description
        name
1 2
0.0 0.0""",
                [(1, 7)],
            ),
            (
                """* description
name
 1 2
0.0 0.0""",
                [(2, 0)],
            ),
            (
                """*description
name
1 2
    0.0     0.0""",
                [],
            ),
            (
                """    *description
        name
            1 2
0.0 0.0""",
                [
                    (0, 3),
                    (1, 7),
                    (2, 11),
                ],
            ),
        ],
    )
    def test_whitespace_is_correctly_logged(
        self, input: str, warnings_description: List[Tuple[int, int]]
    ):
        parser = Parser()

        for l in input.splitlines():
            parser.feed_line(l)

        (_, __, warnings) = parser.finalise()

        assert len(warnings) == len(warnings_description)

        for warning, (line, col) in zip(warnings, warnings_description):
            assert warning.line == (line, line)
            assert warning.column == (0, col)

    @pytest.mark.parametrize(
        "input,warnings_description",
        [
            (
                """*description
name
1 2
0.0 0.0""",
                [],
            ),
            (
                """
* description
name
1 2
0.0 0.0""",
                [(0, 0)],
            ),
            (
                """* description

name
1 2
0.0 0.0""",
                [(1, 1)],
            ),
            (
                """* description



name
1 2
0.0 0.0""",
                [(1, 3)],
            ),
            (
                """* description



name

1 2


0.0 0.0""",
                [(1, 3), (5, 5), (7, 8)],
            ),
        ],
    )
    def test_empty_lines_is_correctly_logged(
        self, input: str, warnings_description: List[Tuple[int, int]]
    ):
        parser = Parser()

        for l in input.splitlines():
            parser.feed_line(l)

        (_, __, warnings) = parser.finalise()

        assert len(warnings) == len(warnings_description)

        for warning, (line_start, line_end) in zip(warnings, warnings_description):
            assert warning.line == (line_start, line_end)

    @pytest.mark.parametrize(
        "input,errors_description",
        [
            (
                "*description",
                [((0, 1), "EoF encountered before the block is finished.")],
            ),
            (
                """*description
not a name""",
                [((0, 2), "Expected a valid name or description at line 1.")],
            ),
            (
                """*description
name
1     """,
                [((0, 3), "Expected valid dimensions at line 2.")],
            ),
            (
                """*description
name
1  5   
1.0 2.0 3.0""",
                [((0, 4), "Expected a valid next point at line 3.")],
            ),
            (
                """*description
name
1  5   
1.0 2.0 3.0 4.0 5.0 6.0""",
                [((0, 4), "Expected a valid next point at line 3.")],
            ),
            (
                """*description
name
1  5   
1.0 2.0 3.0 4.0 5.0
another-name
1 3
1.0 2.0""",
                [((4, 7), "Expected a valid next point at line 6.")],
            ),
            (
                """*description
name
1  5   
1.0 2.0 3.0 4.0 5.0
* 
another-name
1 3
1.0 2.0
* durp
* durp
last-name
1 2
1.0 2.0""",
                [((4, 8), "Expected a valid next point at line 7.")],
            ),
            (
                """*description
name
1  5   
another-name
1 3
1.0 2.0 3.0
* durp
* durp
last-name
1 2
1.0 2.0""",
                [((0, 3), "Expected a valid next point at line 3.")],
            ),
        ],
    )
    def test_invalid_block_is_correctly_logged(
        self, input: str, errors_description: List
    ):
        parser = Parser()

        for l in input.splitlines():
            parser.feed_line(l)

        (_, errors, __) = parser.finalise()

        assert len(errors) == len(errors_description)

        for error, (lines, reason) in zip(errors, errors_description):
            assert error.line == lines
            assert error.reason == reason


@pytest.mark.parametrize(
    "input_value,expected_value",
    [
        (Path("some.pliz"), True),
        (Path("some.pol"), False),
        (Path("some.pli"), False),
        (Path("some.png"), False),
        (Path("some.ext"), False),
        (["some iterator value"], False),
    ],
)
def test_determine_has_z_value(
    input_value: Union[Path, Iterator[str]], expected_value: bool
):
    assert _determine_has_z_value(input_value) == expected_value
