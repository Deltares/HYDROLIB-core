from pathlib import Path

import pytest

from hydrolib.core.io.rr.network.parser import NodeFileParser
from tests.utils import test_input_dir, test_output_dir


class TestNodeFileParser:
    def test_parse_file_does_not_exist_warns(self):

        path = "does/not/exist.tp"

        with pytest.warns(UserWarning) as warning:
            result = NodeFileParser.parse(Path(path))

        actualmessage = warning.list[0].message.args[0]
        assert actualmessage == f"File: `{path}` not found, skipped parsing."
        assert result is not None
        assert len(result) == 0

    def test_parse_parses_file_correctly(self):

        path = Path(test_input_dir / "rr_network" / "3B_NOD.TP")

        result = NodeFileParser.parse(path)

        assert len(result["node"]) == 640
