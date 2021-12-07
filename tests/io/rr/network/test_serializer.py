from pathlib import Path

from hydrolib.core.io.rr.network.serializer import NodeFileSerializer
from tests.utils import assert_files_equal, test_output_dir, test_reference_dir


class TestNodeFileSerializer:
    def test_serialize(self):

        output_file = Path(test_output_dir / "rr" / "serialize.tp")
        reference_file = Path(test_reference_dir / "rr" / "serialize.tp")

        data = dict(
            node=[create_node_values(), create_node_values(), create_node_values()]
        )
        NodeFileSerializer.serialize(output_file, data)

        assert_files_equal(output_file, reference_file)


def create_node_values() -> dict:
    return dict(
        id="node_id",
        nm="node_name",
        ri=1,
        mt=2,
        nt=44,
        ObID="node_obid",
        px=1.23,
        py=2.34,
    )
