import inspect
from pathlib import Path
from typing import Iterator, List, Optional, Tuple, Union

import pytest

from hydrolib.core.basemodel import SerializerConfig
from hydrolib.core.dflowfm.polyfile.models import (
    Description,
    Metadata,
    Point,
    PolyFile,
    PolyObject,
)
from hydrolib.core.dflowfm.polyfile.parser import (
    Block,
    ErrorBuilder,
    InvalidBlock,
    ParseMsg,
    Parser,
    _determine_has_z_value,
    read_polyfile,
)
from hydrolib.core.dflowfm.polyfile.serializer import Serializer, write_polyfile
from tests.utils import assert_files_equal, test_input_dir, test_output_dir


class TestSerializer:
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
    def test_serialize_description(
        self, description: Description, expected_output: str
    ):
        assert (
            "\n".join(Serializer.serialize_description(description)) == expected_output
        )

    @pytest.mark.parametrize(
        "metadata,expected_output",
        [
            (Metadata(name="some-name", n_rows=5, n_columns=10), "some-name\n5    10"),
            (Metadata(name="name", n_rows=25, n_columns=10), "name\n25    10"),
        ],
    )
    def test_serialize_metadata(self, metadata: Metadata, expected_output: str):
        assert "\n".join(Serializer.serialize_metadata(metadata)) == expected_output

    @pytest.mark.parametrize(
        "point,config,expected_output",
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
                SerializerConfig(),
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
                SerializerConfig(float_format=".2f"),
                "    0.00    1.00    2.00    3.00    4.00    5.00",
            ),
            (
                Point(
                    x=0.0,
                    y=1.0,
                    z=None,
                    data=[],
                ),
                SerializerConfig(float_format=".1f"),
                "    0.0    1.0",
            ),
        ],
    )
    def test_serialize_point(
        self, point: Point, config: SerializerConfig, expected_output: str
    ):
        assert Serializer.serialize_point(point, config) == expected_output

    def test_serialize_poly_object(self):
        poly_object = PolyObject(
            description=Description(content=" description\n more description"),
            metadata=Metadata(name="name", n_rows=2, n_columns=2),
            points=[
                Point(x=1.0, y=2.0, z=None, data=[]),
                Point(x=3.0, y=4.0, z=None, data=[]),
            ],
        )

        expected_str = """
            * description
            * more description
            name
            2    2
                1.0    2.0
                3.0    4.0"""
        expected_str = inspect.cleandoc(expected_str)

        assert (
            "\n".join(
                Serializer.serialize_poly_object(poly_object, config=SerializerConfig())
            )
            == expected_str
        )


class TestBlock:
    def test_finalise_valid_state_returns_corresponding_poly_object(self):
        warning_msgs = [ParseMsg(line_start=0, line_end=0, column=None, reason="")]

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

        (result_object, result_warnings) = block.finalize()  # type: ignore
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
        assert block.finalize() is None


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
        assert builder.finalize_previous_error() is None

    def test_finalise_previous_error(self):
        builder = ErrorBuilder()

        line = (0, 20)
        invalid_line = 10
        reason = "reason"
        expected_reason = f"reason at line {invalid_line}."

        builder.start_invalid_block(line[0], invalid_line, reason)
        builder.end_invalid_block(line[1])
        msg = builder.finalize_previous_error()

        assert msg is not None
        assert msg.line_start == line[0]
        assert msg.line_end == line[1]
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
        msg = builder.finalize_previous_error()

        assert msg is not None
        assert msg.line_start == line[0]
        assert msg.line_end == line[1]
        assert msg.reason == expected_reason


class TestParser:
    file_path = Path("dummy.pli")

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
            ("Not a comment but a regular string", True),
            ("Name with spaces", True),
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
            pytest.param(
                "1.0  2.0",
                2,
                False,
                Point(x=1.0, y=2.0, z=None, data=[]),
                id="do not set z-value if has-z is false",
            ),
            pytest.param("1.0  2.0  3.0", 3, True, Point(x=1.0, y=2.0, z=3.0, data=[])),
            pytest.param(
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
                id="set 3rd as data value if has-z is false",
            ),
            pytest.param(
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
                id="set one z-value and remaining in data if has-z is true",
            ),
            pytest.param(
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
                id="set one z-value and remaining in data if has-z is true, supporting whitespace",
            ),
            pytest.param(
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
                id="support int values read as floats",
            ),
            pytest.param(
                "    a    2    3    4    5        ",
                5,
                True,
                None,
                id="no point when first two columns are not numeric",
            ),
            pytest.param(
                "    1.0    2.0    3.0    4.0    5.0        ",
                3,
                True,
                Point(x=1.0, y=2.0, z=3.0, data=[]),
                id="set one z-value and skip superfluous columns",
            ),
            pytest.param(
                "    1.0    2.0    3.0    # comment does not exist, but trailing data is ignored",
                3,
                True,
                Point(x=1.0, y=2.0, z=3.0, data=[]),
                id="set one z-value and comments have no meaning",
            ),
            pytest.param(
                "    1.0    2.0    3.0    4.0 5 As said, trailing data is ignored",
                5,
                True,
                Point(x=1.0, y=2.0, z=3.0, data=[4.0, 5.0]),
                id="set one z-value, 2 data, and skip extra text values without error ",
            ),
            pytest.param(
                "    1.0    2.0    3.0    4.0    5.0        ",
                6,
                True,
                None,
                id="no point when some data columns are missing",
            ),
            pytest.param(
                "1.0,  2.0,",
                2,
                False,
                None,
                id="don't support comma separated values",
            ),
            pytest.param(
                "1.a  2.b",
                2,
                False,
                None,
                id="no point for invalid float values",
            ),
            pytest.param(
                "-1.0  -2.0",
                2,
                False,
                Point(x=-1.0, y=-2.0, z=None, data=[]),
                id="support negative values",
            ),
        ],
    )
    def test_convert_to_point(
        self, input: str, n_total_points: int, has_z: bool, expected_value: Point
    ):
        assert Parser._convert_to_point(input, n_total_points, has_z) == expected_value

    def test_correct_pli_expected_result(self, recwarn):
        input_data = inspect.cleandoc(
            """
            * Some header
            * with multiple
            * descriptions
            the-name
            2    3
                1.0 2.0 3.0
                4.0 5.0 6.0
            another-name
            3    2
                7.0   8.0
                9.0  10.0
               11.0  12.0"""
        )

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

        parser = Parser(self.file_path, has_z_value=False)

        for l in input_data.splitlines():
            parser.feed_line(l)

        poly_objects = parser.finalize()

        assert len(recwarn) == 0
        assert poly_objects == expected_poly_objects

    @pytest.mark.parametrize(
        "input,warnings_description",
        [
            (
                inspect.cleandoc(
                    """
                    *description
                    name
                    1 2
                    0.0 0.0"""
                ),
                [],
            ),
            (
                # No cleandoc here because we explicitly want the empty line
                # at the start
                """
* description
name
1 2
0.0 0.0""",
                [(0, 0)],
            ),
            (
                inspect.cleandoc(
                    """
                    * description

                    name
                    1 2
                    0.0 0.0"""
                ),
                [(1, 1)],
            ),
            (
                inspect.cleandoc(
                    """
                    * description



                    name
                    1 2
                    0.0 0.0"""
                ),
                [(1, 3)],
            ),
            (
                inspect.cleandoc(
                    """
                    * description



                    name

                    1 2


                    0.0 0.0"""
                ),
                [(1, 3), (5, 5), (7, 8)],
            ),
        ],
    )
    def test_empty_lines_is_correctly_logged(
        self, input: str, warnings_description: List[Tuple[int, int]], recwarn
    ):
        parser = Parser(self.file_path)

        for l in input.splitlines():
            parser.feed_line(l)

        _ = parser.finalize()

        assert len(recwarn) == len(warnings_description)

        for warning, (line_start, line_end) in zip(recwarn, warnings_description):
            block_suffix = (
                f"Invalid block {line_start}:{line_end}"
                if line_start != line_end
                else f"Invalid line {line_start}"
            )

            found_msg = warning.message.args[0]
            expected_msg = (
                f"Empty lines are ignored.\n{block_suffix}\nFile: {self.file_path}"
            )
            assert found_msg == expected_msg

    @pytest.mark.parametrize(
        "input,expected_msg_data",
        [
            (
                "*description",
                [((0, 1), "EoF encountered before the block is finished.")],
            ),
            (
                inspect.cleandoc(
                    """
                    *description
                    name
                    2  5
                    1.0 2.0 3.0 4.0 5.0"""
                ),
                [((0, 4), "EoF encountered before the block is finished.")],
            ),
            (
                inspect.cleandoc(
                    """
                    *description
                    name
                    1  5
                    1.0 2.0 3.0 4.0 5.0
                    2.0 3.0 4.0 5.0 6.0"""
                ),
                [
                    (
                        (4, 5),
                        "EoF encountered before the block is finished.",
                    )
                ],
            ),
            (
                inspect.cleandoc(
                    """
                    *description
                    name
                    1     """
                ),
                [((0, 3), "Expected valid dimensions at line 2.")],
            ),
            (
                inspect.cleandoc(
                    """
                    *description
                    name
                    1  5
                    1.0 2.0 3.0"""
                ),
                [((0, 4), "Expected a valid next point at line 3.")],
            ),
            (
                inspect.cleandoc(
                    """
                    *description
                    name
                    1  5
                        1.0 2.0 3.0 4.0 5.0
                    another-name
                    1 3
                        1.0 2.0"""
                ),
                [((4, 7), "Expected a valid next point at line 6.")],
            ),
            (
                inspect.cleandoc(
                    """
                    *description
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
                    1.0 2.0"""
                ),
                [((4, 9), "Expected a valid next point at line 7.")],
            ),
            (
                inspect.cleandoc(
                    """
                    *description
                    name
                    1  5
                    another-name
                    1 3
                    1.0 2.0 3.0
                    * durp
                    * durp
                    last-name
                    1 2
                    1.0 2.0"""
                ),
                [((0, 3), "Expected a valid next point at line 3.")],
            ),
            (
                inspect.cleandoc(
                    """
                    *description
                    name
                    1  5
                    # 1.0 2.0 3.0 4.0 5.0 Comment after the values is valid"""
                ),
                [((0, 4), "Expected a valid next point at line 3.")],
            ),
        ],
    )
    def test_invalid_block_correctly_raises_error(
        self, input: str, expected_msg_data: str
    ):
        parser = Parser(self.file_path)

        with pytest.raises(ValueError) as error:
            for l in input.splitlines():
                parser.feed_line(l)

            _ = parser.finalize()

        found_msg = error.value.args[0]
        expected_affected_blocks_of_error_msg = expected_msg_data[0][0]
        expected_part_of_error_msg = expected_msg_data[0][1]
        expected_error_msg = f"Invalid formatted plifile, {expected_part_of_error_msg}\nInvalid block {expected_affected_blocks_of_error_msg[0]}:{expected_affected_blocks_of_error_msg[1]}\nFile: dummy.pli"
        assert found_msg == expected_error_msg

    def test_polyfile_can_be_saved_without_errors_and_is_same_as_input(self):
        infile = test_input_dir / "dflowfm_individual_files" / "test.pli"
        outfile = test_output_dir / "test.pli"

        polyfile = PolyFile(filepath=infile)
        polyfile.save(filepath=outfile)

        assert_files_equal(infile, outfile)


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


def test_write_read_write_should_have_the_same_data():
    path = test_output_dir / "tmp" / "test.pliz"

    objects = [
        PolyObject(
            description=None,
            metadata=Metadata(name="someName", n_rows=2, n_columns=3),
            points=[
                Point(x=0.0, y=1.0, z=2.0, data=[]),
                Point(x=0.01, y=1.01, z=2.01, data=[]),
            ],
        ),
        PolyObject(
            description=Description(content=" header"),
            metadata=Metadata(name="014", n_rows=3, n_columns=4),
            points=[
                Point(x=0.0, y=1.0, z=2.0, data=[1.0]),
                Point(x=0.01, y=1.01, z=2.01, data=[2.0]),
                Point(x=5.01, y=6.01, z=7.01, data=[2.0]),
            ],
        ),
        PolyObject(
            description=Description(content=" header"),
            metadata=Metadata(name="014", n_rows=5, n_columns=4),
            points=[
                Point(x=0.0, y=1.0, z=2.0, data=[1.0]),
                Point(x=0.01, y=1.01, z=2.01, data=[2.0]),
                Point(x=5.01, y=-6.01, z=-7.01, data=[2.0]),
                Point(x=0.0, y=-1.0, z=2.0, data=[1.0]),
                Point(x=-0.01, y=1.01, z=2.01, data=[2.0]),
            ],
        ),
    ]

    write_polyfile(path, objects, config=SerializerConfig())
    read_result = read_polyfile(path, has_z_values=True)

    assert read_result["objects"] == objects
    assert read_result["has_z_values"] == True
