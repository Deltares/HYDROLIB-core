import pytest

from hydrolib.core.base.models import ModelSaveSettings, SerializerConfig
from hydrolib.core.dflowfm.xyn.models import XYNModel, XYNPoint
from hydrolib.core.dflowfm.xyn.parser import XYNParser
from hydrolib.core.dflowfm.xyn.serializer import XYNSerializer
from tests.utils import create_temp_file, get_temp_file

from ..utils import (
    assert_files_equal,
    create_temp_file,
    create_temp_file_from_lines,
    get_temp_file,
)


class TestXYNParser:
    def test_parse_xyn_file(self):
        file_content = """
            *This is a comment and should not be parsed.
            1.1 2.2 'ObservationPoint_2D_01'
            3.3 4.4 "ObservationPoint_2D_02"
        """

        expected_result = {
            "points": [
                {"x": "1.1", "y": "2.2", "n": "ObservationPoint_2D_01"},
                {"x": "3.3", "y": "4.4", "n": "ObservationPoint_2D_02"},
            ]
        }

        with create_temp_file(file_content, "test.xyn") as xyn_file:
            parsed_contents = XYNParser.parse(xyn_file)
        assert expected_result == parsed_contents

    def test_parse_xyn_file_with_single_quoted_name_removes_quotes_and_keeps_whitespace(
        self,
    ):
        file_content = """
            1.1 2.2 'ObservationPoint 2D 01'
        """

        expected_result = {
            "points": [
                {"x": "1.1", "y": "2.2", "n": "ObservationPoint 2D 01"},
            ]
        }

        with create_temp_file(file_content, "test.xyn") as xyn_file:
            parsed_contents = XYNParser.parse(xyn_file)
        assert expected_result == parsed_contents

    def test_parse_xyn_file_with_double_quoted_name_removes_quotes_and_keeps_whitespace(
        self,
    ):
        file_content = """
            1.1 2.2 "ObservationPoint 2D 01"
        """

        expected_result = {
            "points": [
                {"x": 1.1, "y": 2.2, "n": "ObservationPoint 2D 01"},
            ]
        }

        with create_temp_file(file_content, "test.xyn") as xyn_file:
            parsed_contents = XYNParser.parse(xyn_file)

        assert expected_result == parsed_contents

    def test_parse_xyn_file_with_too_many_columns_raises_error(self):
        name = "'ObservationPoint_2D_01' This is too much content"
        file_content = f"1.1 2.2 {name}"

        with pytest.raises(ValueError) as error:
            with create_temp_file(file_content, "test.xyn") as xyn_file:
                expected_message = f"Error parsing XYN file '{xyn_file}', line 1. Name `{name}` contains whitespace, so should be enclosed in quotes."
                _ = XYNParser.parse(xyn_file)

        assert expected_message in str(error.value)


class TestXYNSerializer:
    def test_serialize_xyn_point(self):
        expected_file_content = ["1.10 2.20 randomName\n", "3.30 4.40 'randomName 2'"]

        data = {
            "points": [
                {"x": 1.10, "y": 2.20, "n": "randomName"},
                {"x": 3.30, "y": 4.40, "n": "randomName 2"},
            ]
        }

        config = SerializerConfig(float_format=".2f")
        save_settings = ModelSaveSettings()

        with get_temp_file("test.xyn") as xyn_file:
            XYNSerializer.serialize(xyn_file, data, config, save_settings)

            with open(xyn_file) as file:
                file_content = file.readlines()
        assert file_content == expected_file_content


class TestXYNModel:
    def test_initialization(self):
        model = XYNModel()

        assert len(model.points) == 0

    def test_load_model(self):
        file_content = [
            "* This is a comment.",
            "1.1 2.2 'randomName1'",
            "3.3 4.4 'randomName2'",
        ]

        with create_temp_file_from_lines(file_content, "test.xyn") as temp_file:
            model = XYNModel(filepath=temp_file)

        expected_points = [
            XYNPoint(x=1.1, y=2.2, n="randomName1"),
            XYNPoint(x=3.3, y=4.4, n="randomName2"),
        ]

        assert model.points == expected_points

    def test_save_model(self):
        points = [
            {"x": 1.1, "y": 2.2, "n": "randomName1"},
            {"x": 3.3, "y": 4.4, "n": "randomName2"},
        ]

        model = XYNModel(points=points)

        with get_temp_file("test.xyn") as actual_file:
            model.save(filepath=actual_file)

            expected_file_content = [
                "1.1 2.2 randomName1",
                "3.3 4.4 randomName2",
            ]

            with create_temp_file_from_lines(
                expected_file_content, "expected.xyn"
            ) as expected_file:
                assert_files_equal(actual_file, expected_file)


class TestXYNPoint:
    @pytest.mark.parametrize(
        ("name"),
        [
            pytest.param("nameWith'SingleQuote", id="Name with single quote"),
            pytest.param('nameWith"DoubleQuote', id="Name with double quote"),
            pytest.param(None, id="None value"),
            pytest.param("", id="Empty string"),
            pytest.param("     ", id="Whitespace only"),
        ],
    )
    def test_validate_name_raises_error_on_invalid_name(self, name: str):
        with pytest.raises(ValueError):
            _ = XYNPoint(x=1.1, y=2.2, n=name)
