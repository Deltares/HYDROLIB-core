from hydrolib.core.io.rr.network.models import Node, NodeFile


class TestNode:
    def test_create_node(self):
        node = Node(**create_node_values())

        assert node.id == "node_id"
        assert node.nm == "node_name"
        assert node.ri == 1
        assert node.mt == 2
        assert node.nt == 3
        assert node.obid == "node_obid"
        assert node.px == 1.23
        assert node.py == 2.34


class TestNodeFile:
    def test_create_nodefile(self):
        nodefile_values = dict(node=[create_node_values()])

        nodefile = NodeFile(**nodefile_values)

        assert len(nodefile.node) == 1
        assert nodefile.node[0].id == "node_id"


def create_node_values() -> dict:
    return dict(
        id="node_id",
        nm="node_name",
        ri=1,
        mt=2,
        nt=3,
        ObId="node_obid",
        px=1.23,
        py=2.34,
    )
