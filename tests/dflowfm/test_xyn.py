import pytest

from hydrolib.core.basemodel import ModelSaveSettings, SerializerConfig
from hydrolib.core.dflowfm.xyn.models import XYNModel, XYNPoint
from hydrolib.core.dflowfm.xyn.name_validator import NameValidator
from hydrolib.core.dflowfm.xyn.parser import XYNParser
from hydrolib.core.dflowfm.xyn.serializer import XYNSerializer

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
            3.3 4.4 'ObservationPoint_2D_02'
        """

        expected_result = {
            "points": [
                {"x": "1.1", "y": "2.2", "n": "'ObservationPoint_2D_01'"},
                {"x": "3.3", "y": "4.4", "n": "'ObservationPoint_2D_02'"},
            ]
        }

        with create_temp_file(file_content, "test.xyn") as xyn_file:
            parsed_contents = XYNParser.parse(xyn_file)
            assert expected_result == parsed_contents


class TestXYNSerializer:
    def test_serialize_xyn_point(self):
        expected_file_content = ["1.10 2.20 randomName\n", "3.30 4.40 'randomName 2'\n"]

        data = {
            "points": [
                XYNPoint(x=1.1, y=2.2, n="randomName"),
                XYNPoint(x=3.3, y=4.4, n="'randomName 2'"),
            ]
        }

        config = SerializerConfig(float_format=".2f")
        save_settings = ModelSaveSettings()

        with get_temp_file("test.xyn") as xyn_file:
            XYNSerializer.serialize(xyn_file, data, config, save_settings)

            with open(xyn_file) as file:
                file_content = file.readlines()
                assert file_content == expected_file_content


class TestNameValidator:
    @pytest.mark.parametrize(
        ("input", "expected_output"),
        [
            pytest.param("randomName", "randomName", id="Name without spaces"),
            pytest.param(
                "'random name'", "random name", id="Name with spaces and quotes"
            ),
            pytest.param("    randomName   ", "randomName", id="Name with whitespace"),
            pytest.param(
                "'  randomName '", "  randomName ", id="Name with whitespace and quotes"
            ),
            pytest.param("#randomName", "#randomName", id="Name starting with hashtag"),
            pytest.param(
                "'#randomName'",
                "#randomName",
                id="Name with quotes starting with hashtag",
            ),
        ],
    )
    def test_validate_name(self, input: str, expected_output: str):
        output = NameValidator.validate(input)
        assert output == expected_output

    @pytest.mark.parametrize(
        ("input"),
        [
            pytest.param("'random name", id="Name with only starting quote"),
            pytest.param("random name'", id="Name with only ending quote"),
            pytest.param(None, id="None value"),
            pytest.param("", id="Empty string"),
            pytest.param("''", id="Empty string with quotes"),
            pytest.param("     ", id="Whitespace only"),
            pytest.param("'     '", id="Whitespace only with quotes"),
            pytest.param("randomName #randomComment", id="Name followed by comment"),
            pytest.param(
                "randomName bla bla bla",
                id="Name followed by additional content",
            ),
            pytest.param(
                "'randomName' bla bla bla",
                id="Name with quotes followed by additional content",
            ),
            pytest.param(
                "randomNameWithQuote'InIt",
                id="Name that contains a quote",
            ),
            pytest.param(
                "'randomNameWithQuote'InIt'",
                id="Name with quotes that contains a quote",
            ),
        ],
    )
    def test_validate_invalid_name_raises_error(self, input: str):
        with pytest.raises(ValueError):
            _ = NameValidator.validate(input)


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
            XYNPoint(x=1.1, y=2.2, n="randomName1"),
            XYNPoint(x=3.3, y=4.4, n="randomName2"),
        ]

        model = XYNModel(points=points)

        with get_temp_file("test.xyn") as actual_file:
            model.save(filepath=actual_file)

            expected_file_content = [
                "1.1 2.2 randomName1",
                "3.3 4.4 randomName2",
                "",
            ]

            with create_temp_file_from_lines(
                expected_file_content, "expected.xyn"
            ) as expected_file:
                assert_files_equal(actual_file, expected_file)


class TestXYNPoint:
    def test_new_xyn_point_with_invalid_name_should_raise_error(self):
        invalid_name = "Invalid name"

        with pytest.raises(ValueError) as error:
            _ = XYNPoint(x=1.1, y=2.2, n=invalid_name)
            expected_message = "Name cannot contain spaces."
            assert expected_message in str(error.value)

    def test_new_xyn_point_with_valid_name(self):
        valid_name = "'Valid name'"
        point = XYNPoint(x=1.1, y=2.2, n=valid_name)

        assert point.n == "Valid name"

    def test_update_xyn_point_to_invalid_name_should_raise_error(self):
        invalid_name = "Invalid name"

        point = XYNPoint(x=1.1, y=2.2, n="'valid name'")

        with pytest.raises(ValueError) as error:
            point.n = invalid_name

            expected_message = "Name cannot contain spaces."
            assert expected_message in str(error.value)
