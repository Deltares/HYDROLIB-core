from pathlib import Path

import pytest

from hydrolib.core.io.rr.network.parser import NodeFileParser
from tests.utils import test_input_dir


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

        assert len(result) == 1
        assert len(result["node"]) == 640

        node = result["node"][7]
        assert node["id"] == "'unp_AFW_BOM200-P_1386'"
        assert node["nm"] == "'unp_AFW_BOM200-P_1386'"
        assert node["ri"] == "'-1'"
        assert node["mt"] == "'2'"
        assert node["nt"] == "44"
        assert node["ObID"] == "'3B_UNPAVED'"
        assert node["px"] == "133860"
        assert node["py"] == "422579"
