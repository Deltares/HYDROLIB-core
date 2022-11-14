from pathlib import Path
from hydrolib.core.basemodel import SerializerConfig

from hydrolib.core.io.rr.topology.serializer import (
    LinkFileSerializer,
    NodeFileSerializer,
)
from tests.utils import assert_files_equal, test_output_dir, test_reference_dir


class TestNodeFileSerializer:
    def test_serialize(self):

        output_file = Path(test_output_dir / "rr" / "serialize_node.tp")
        reference_file = Path(test_reference_dir / "rr" / "serialize_node.tp")

        data = dict(
            node=[create_node_values(), create_node_values(), create_node_values()]
        )
        NodeFileSerializer.serialize(output_file, data, config=SerializerConfig())

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


class TestLinkFileSerializer:
    def test_serialize(self):

        output_file = Path(test_output_dir / "rr" / "serialize_link.tp")
        reference_file = Path(test_reference_dir / "rr" / "serialize_link.tp")

        data = dict(
            link=[create_link_values(), create_link_values(), create_link_values()]
        )
        LinkFileSerializer.serialize(output_file, data, config=SerializerConfig())

        assert_files_equal(output_file, reference_file)


def create_link_values() -> dict:
    return dict(
        id="link_id",
        nm="link_name",
        ri=1,
        mt=2,
        bt=3,
        ObID="link_obid",
        bn="link_beginnode",
        en="link_endnode",
    )
