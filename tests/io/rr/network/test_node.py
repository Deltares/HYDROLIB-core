from pathlib import Path

import pytest
from pydantic.error_wrappers import ValidationError

from hydrolib.core.io.rr.network.models import Node, NodeFile
from tests.utils import (
    assert_files_equal,
    test_input_dir,
    test_output_dir,
    test_reference_dir,
)


class TestNode:
    def test_create_node(self):
        node = Node(**create_node_values())

        assert node.id == "node_id"
        assert node.name == "node_name"
        assert node.branchid == 1
        assert node.modelnodetype == 2
        assert node.netternodetype == 44
        assert node.objectid == "node_obid"
        assert node.xposition == 1.23
        assert node.yposition == 2.34

    @pytest.mark.parametrize(
        "key, value, exp_message",
        [
            (
                "mt",
                99,
                "99 is not a supported model node type (mt). Supported values:",
            ),
            (
                "nt",
                99,
                "99 is not a supported netter node type (nt). Supported values:",
            ),
            (
                "mt",
                3,
                "3 is not a supported model node type (mt) when netter node type (nt) is 44. Supported value: 2.",
            ),
        ],
    )
    def test_validate_unsupported_modelnodetype(
        self, key: str, value: int, exp_message: str
    ):
        values = create_node_values()
        values[key] = value

        with pytest.raises(ValidationError) as error:
            Node(**values)

        assert exp_message in str(error.value)

    def test_skip_validation_modelnodetype6(self):
        values = create_node_values()
        values["mt"] = 6
        values["nt"] = 99

        try:
            Node(**values)
        except ValidationError as error:
            raise pytest.fail(f"Validation failed for mt = 6: {error}")


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

    def test_save(self):

        output_file = Path(test_output_dir / "rr" / "serialize_node.tp")
        reference_file = Path(test_reference_dir / "rr" / "serialize_node.tp")

        node = Node(**create_node_values())
        nodefile = NodeFile(node=[node, node, node])
        nodefile.filepath = output_file

        nodefile.save()

        assert_files_equal(output_file, reference_file)

    def test_to_dict(self):
        data = create_node_values()
        node = Node(**data)

        result = node.dict()

        assert result == data


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
