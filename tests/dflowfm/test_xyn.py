from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import contextmanager
import pytest

from hydrolib.core.dflowfm.xyn.parser import XYNParser


class TestXYNParser:
    def test_parse_xyn_file(self):
        file_content = """1.1 2.2 'ObservationPoint_2D_01'
                          3.3 4.4 'ObservationPoint_2D_02'"""

        expected_result = {
            "points": [
                {"x": "1.1", "y": "2.2", "n": "ObservationPoint_2D_01"},
                {"x": "3.3", "y": "4.4", "n": "ObservationPoint_2D_02"},
            ]
        }

        with TestXYNParser._create_temp_xyn_file(file_content) as xyn_file:
            parsed_contents = XYNParser.parse(xyn_file)
            assert expected_result == parsed_contents

    @pytest.mark.parametrize(
        "file_content",
        [
            pytest.param(
                """1.1 2.2 'ObservationPoint_2D_01' # comments are not supported
                   3.3 4.4 'ObservationPoint_2D_02'""",
                id="Comments are not supported",
            )
        ],
    )
    def test_parse_xyn_file_with_unexpected_content_raises_error(
        self, file_content: str
    ):
        with TestXYNParser._create_temp_xyn_file(file_content) as xyn_file:
            with pytest.raises(ValueError) as error:
                _ = XYNParser.parse(xyn_file)

            expected_message = "Error parsing XYN file 'test.xyn', line 1."
            assert expected_message in str(error.value)

    @contextmanager
    def _create_temp_xyn_file(content: str):
        with TemporaryDirectory() as temp_dir:
            xyn_file = Path(temp_dir, "test.xyn")
            with open(xyn_file, "w") as f:
                f.write(content)
            yield xyn_file
