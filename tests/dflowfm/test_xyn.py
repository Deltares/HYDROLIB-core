from contextlib import contextmanager
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from hydrolib.core.basemodel import SerializerConfig
from hydrolib.core.dflowfm.xyn.models import XYNPoint
from hydrolib.core.dflowfm.xyn.name_extrator import NameExtractor
from hydrolib.core.dflowfm.xyn.parser import XYNParser
from hydrolib.core.dflowfm.xyn.serializer import XYNSerializer


class TestXYNParser:
    def test_parse_xyn_file(self):
        file_content = """
            *This is a comment and should not be parsed.
            1.1 2.2 'ObservationPoint_2D_01' #This comment should be ignored as well!
            3.3 4.4 'ObservationPoint_2D_02'
        """

        expected_result = {
            "points": [
                {"x": "1.1", "y": "2.2", "n": "ObservationPoint_2D_01"},
                {"x": "3.3", "y": "4.4", "n": "ObservationPoint_2D_02"},
            ]
        }

        with TestXYNParser._create_temp_xyn_file(file_content) as xyn_file:
            parsed_contents = XYNParser.parse(xyn_file)
            assert expected_result == parsed_contents

    @classmethod
    @contextmanager
    def _create_temp_xyn_file(cls, content: str):
        with TemporaryDirectory() as temp_dir:
            xyn_file = Path(temp_dir, "test.xyn")
            with open(xyn_file, "w") as f:
                f.write(content)
            yield xyn_file


class TestXYNSerializer:
    def test_serialize_xyn_point(self):
        expected_file_content = ["1.10 2.20 randomName\n", "3.30 4.40 'randomName 2'\n"]

        data = {
            "points": [
                XYNPoint(x=1.1, y=2.2, n="randomName"),
                XYNPoint(x=3.3, y=4.4, n="randomName 2"),
            ]
        }

        config = SerializerConfig(float_format=".2f")

        with TestXYNSerializer._create_temp_xyn_file() as xyn_file:
            XYNSerializer.serialize(xyn_file, data, config)

            with open(xyn_file) as file:
                file_content = file.readlines()
                assert file_content == expected_file_content

    @classmethod
    @contextmanager
    def _create_temp_xyn_file(cls):
        with TemporaryDirectory() as temp_dir:
            yield Path(temp_dir, "test.xyn")


class TestNameExtractor:
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
            pytest.param(
                "randomName #randomComment", "randomName", id="Name followed by comment"
            ),
        ],
    )
    def test_extract_name(self, input: str, expected_output: str):
        output = NameExtractor.extract_name(input)
        assert output == expected_output

    @pytest.mark.parametrize(
        ("input"),
        [
            pytest.param("#randomName", id="Name starting with hashtag"),
            pytest.param("'#randomName'", id="Name with quotes starting with hashtag"),
            pytest.param("random name", id="Name with spaces without quotes"),
            pytest.param("'random name", id="Name with only starting quote"),
            pytest.param("random name'", id="Name with only ending quote"),
            pytest.param(None, id="None value"),
            pytest.param("", id="Empty string"),
            pytest.param("''", id="Empty string with quotes"),
            pytest.param("     ", id="Whitespace only"),
            pytest.param("'     '", id="Whitespace only with quotes"),
        ],
    )
    def test_extract_invalid_name_raises_error(self, input: str):
        with pytest.raises(ValueError):
            _ = NameExtractor.extract_name(input)
