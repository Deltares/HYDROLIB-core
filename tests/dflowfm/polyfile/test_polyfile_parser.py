import inspect
from pathlib import Path
from typing import List, Optional, Tuple

import pytest

from hydrolib.core.dflowfm.polyfile.models import Description, Metadata, PolyFile
from hydrolib.core.dflowfm.polyfile.parser import Parser, Point, PolyObject
from tests.utils import assert_files_equal, test_input_dir, test_output_dir

file_path = Path("dummy.pli")


@pytest.mark.parametrize(
    "input_string,expected_value",
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
def test_is_comment(input_string: str, expected_value: bool):
    assert Parser._is_comment(input_string) == expected_value


@pytest.mark.parametrize(
    "input_string,expected_value",
    [
        ("* some comment", " some comment"),
        ("*", ""),
        ("*   ", ""),
    ],
)
def test_convert_to_comment(input_string: str, expected_value: str):
    assert Parser._convert_to_comment(input_string) == expected_value


@pytest.mark.parametrize(
    "input_string,expected_value",
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
def test_is_name(input_string: str, expected_value: bool):
    assert Parser._is_name(input_string) == expected_value


@pytest.mark.parametrize(
    "input_string,expected_value",
    [
        ("potato", "potato"),
        ("    potato     ", "potato"),
        ("1_1  ", "1_1"),
        ("1_1:type=terrainjump", "1_1:type=terrainjump"),
    ],
)
def test_convert_to_name(input_string: str, expected_value: str):
    assert Parser._convert_to_name(input_string) == expected_value


@pytest.mark.parametrize(
    "input_string,expected_value",
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
    input_string: str, expected_value: Optional[Tuple[int, int]]
):
    assert Parser._convert_to_dimensions(input_string) == expected_value


@pytest.mark.parametrize(
    "input_string,n_total_points,has_z,expected_value",
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
    input_string: str, n_total_points: int, has_z: bool, expected_value: Point
):
    assert (
        Parser._convert_to_point(input_string, n_total_points, has_z) == expected_value
    )


def test_correct_pli_expected_result(recwarn):
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

    parser = Parser(file_path, has_z_value=False)

    for l in input_data.splitlines():
        parser.feed_line(l)

    poly_objects = parser.finalize()

    assert len(recwarn) == 0
    assert poly_objects == expected_poly_objects


@pytest.mark.parametrize(
    "input_string,warnings_description",
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
    input_string: str, warnings_description: List[Tuple[int, int]], recwarn
):
    parser = Parser(file_path)

    for l in input_string.splitlines():
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
        expected_msg = f"Empty lines are ignored.\n{block_suffix}\nFile: {file_path}"
        assert found_msg == expected_msg


@pytest.mark.parametrize(
    "input_string,expected_msg_data",
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
    input_string: str, expected_msg_data: str
):
    parser = Parser(file_path)

    with pytest.raises(ValueError) as error:
        for l in input_string.splitlines():
            parser.feed_line(l)

        _ = parser.finalize()

    found_msg = error.value.args[0]
    expected_affected_blocks_of_error_msg = expected_msg_data[0][0]
    expected_part_of_error_msg = expected_msg_data[0][1]
    expected_error_msg = f"Invalid formatted plifile, {expected_part_of_error_msg}\nInvalid block {expected_affected_blocks_of_error_msg[0]}:{expected_affected_blocks_of_error_msg[1]}\nFile: dummy.pli"
    assert found_msg == expected_error_msg


def test_polyfile_can_be_saved_without_errors_and_is_same_as_input():
    infile = test_input_dir / "dflowfm_individual_files" / "test.pli"
    outfile = test_output_dir / "test.pli"

    polyfile = PolyFile(filepath=infile)
    polyfile.save(filepath=outfile)

    assert_files_equal(infile, outfile)
