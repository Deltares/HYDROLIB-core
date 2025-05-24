from pathlib import Path

from hydrolib.core.base.models import ModelSaveSettings, SerializerConfig
from hydrolib.core.rr.topology.serializer import LinkFileSerializer, NodeFileSerializer
from tests.utils import assert_files_equal


class TestNodeFileSerializer:
    def test_serialize(self, output_files_dir: Path, reference_files_dir: Path):

        output_file = output_files_dir.joinpath("rr/serialize_node.tp")
        reference_file = reference_files_dir.joinpath("rr/serialize_node.tp")

        data = dict(
            node=[create_node_values(), create_node_values(), create_node_values()]
        )
        config = SerializerConfig(float_format=".3f")
        NodeFileSerializer.serialize(
            output_file, data, config, save_settings=ModelSaveSettings()
        )

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
    def test_serialize(self, output_files_dir: Path, reference_files_dir: Path):

        output_file = output_files_dir.joinpath("rr/serialize_link.tp")
        reference_file = reference_files_dir.joinpath("rr/serialize_link.tp")

        data = dict(
            link=[create_link_values(), create_link_values(), create_link_values()]
        )
        LinkFileSerializer.serialize(
            output_file,
            data,
            config=SerializerConfig(),
            save_settings=ModelSaveSettings(),
        )

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
