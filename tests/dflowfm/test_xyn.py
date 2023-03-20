from pathlib import Path
from tempfile import TemporaryDirectory
from contextlib import contextmanager

from hydrolib.core.dflowfm.xyn.parser import XYNParser


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

    @contextmanager
    def _create_temp_xyn_file(content: str):
        with TemporaryDirectory() as temp_dir:
            xyn_file = Path(temp_dir, "test.xyn")
            with open(xyn_file, "w") as f:
                f.write(content)
            yield xyn_file
