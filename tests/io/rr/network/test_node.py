from pathlib import Path

from hydrolib.core.io.rr.network.models import Node, NodeFile
from tests.utils import test_input_dir


class TestNode:
    def test_create_node(self):
        node = Node(**create_node_values())

        assert node.id == "node_id"
        assert node.name == "node_name"
        assert node.branchid == 1
        assert node.modelnodetype == 2
        assert node.netternodetype == 3
        assert node.objectid == "node_obid"
        assert node.xposition == 1.23
        assert node.yposition == 2.34


class TestNodeFile:
    def test_create_nodefile(self):
        nodefile_values = dict(node=[create_node_values()])

        nodefile = NodeFile(**nodefile_values)

        assert len(nodefile.node) == 1
        assert nodefile.node[0].id == "node_id"

    def test_load_from_file(self):

        path = Path(test_input_dir / "rr_network" / "3B_NOD.TP")

        nodefile = NodeFile(filepath=path)

        assert len(nodefile.node) == 640

        node = nodefile.node[7]
        assert node.id == "unp_AFW_BOM200-P_1386"
        assert node.name == "unp_AFW_BOM200-P_1386"
        assert node.branchid == -1
        assert node.modelnodetype == 2
        assert node.netternodetype == 44
        assert node.objectid == "3B_UNPAVED"
        assert node.xposition == 133860
        assert node.yposition == 422579


def create_node_values() -> dict:
    return dict(
        id="node_id",
        nm="node_name",
        ri=1,
        mt=2,
        nt=3,
        ObID="node_obid",
        px=1.23,
        py=2.34,
    )
