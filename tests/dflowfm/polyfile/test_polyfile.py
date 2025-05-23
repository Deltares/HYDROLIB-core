import inspect
from pathlib import Path
from typing import Iterator, List, Optional, Tuple, Union

import pytest

from hydrolib.core.basemodel import SerializerConfig
from hydrolib.core.dflowfm.polyfile.models import (
    Description,
    Metadata,
    Point,
    PolyObject,
)
from hydrolib.core.dflowfm.polyfile.parser import (
    Block,
    ErrorBuilder,
    InvalidBlock,
    ParseMsg,
    _determine_has_z_value,
    read_polyfile,
)
from hydrolib.core.dflowfm.polyfile.serializer import Serializer, write_polyfile
from tests.utils import test_output_dir


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
