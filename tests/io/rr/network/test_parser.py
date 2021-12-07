from pathlib import Path

import pytest

from hydrolib.core.io.net.models import Network
from hydrolib.core.io.rr.network.parser import NetworkTopologyFileParser
from tests.utils import test_input_dir


class TestNodeFileParser:
    def test_parse_file_does_not_exist_warns(self):

        path = Path("does/not/exist.tp")
        parser = NetworkTopologyFileParser("node")

        with pytest.warns(UserWarning) as warning:
            result = parser.parse(path)

        actualmessage = warning.list[0].message.args[0]
        assert actualmessage == f"File: `{path}` not found, skipped parsing."
        assert result is not None
        assert len(result) == 0

    def test_parse_parses_file_correctly(self):

        path = Path(test_input_dir / "rr_network" / "3B_NOD.TP")
        parser = NetworkTopologyFileParser("node")

        result = parser.parse(path)

        assert len(result) == 1
        assert len(result["node"]) == 640

        node = result["node"][7]
        assert node["id"] == "unp_AFW_BOM200-P_1386"
        assert node["nm"] == "unp_AFW_BOM200-P_1386"
        assert node["ri"] == "-1"
        assert node["mt"] == "2"
        assert node["nt"] == "44"
        assert node["ObID"] == "3B_UNPAVED"
        assert node["px"] == "133860"
        assert node["py"] == "422579"

    @pytest.mark.parametrize(
        "input_file",
        ["3B_NOD_format1.TP", "3B_NOD_format2.TP", "3B_NOD_format3.TP"],
    )
    def test_parse_parses_file_correctly(self, input_file: str):

        path = Path(test_input_dir / "rr_network" / input_file)
        parser = NetworkTopologyFileParser("node")
        
        result = parser.parse(path)

        assert len(result) == 1
        assert len(result["node"]) == 3

        node = result["node"][1]
        assert node["id"] == "unp_AFW_BOM200-P_1606"
        assert node["nm"] == "unp_AFW_BOM200-P_1606"
        assert node["ri"] == "-1"
        assert node["mt"] == "2"
        assert node["nt"] == "44"
        assert node["ObID"] == "3B_UNPAVED"
        assert node["px"] == "136207"
        assert node["py"] == "423934"
