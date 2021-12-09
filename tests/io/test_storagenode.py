import pytest
from pydantic.error_wrappers import ValidationError

from hydrolib.core.io.storagenode.models import (
    Interpolation,
    NodeType,
    StorageNode,
    StorageType,
)


class TestStorageNode:
    def test_create_storage_node_usetable_true(self):
        vals = _create_storage_node_values(usetable=True)
        storagenode = StorageNode(**vals)

        assert storagenode.id == "storagenode_id"
        assert storagenode.name == "storagenode_name"
        assert storagenode.manholeid == "manhole_id"
        assert storagenode.nodetype == NodeType.soakawaydrain
        assert storagenode.nodeid == "node_id"

        assert storagenode.usetable == True

        assert storagenode.bedlevel == None
        assert storagenode.area == None
        assert storagenode.streetlevel == None
        assert storagenode.streetstoragearea == None
        assert storagenode.storagetype == StorageType.reservoir

        assert storagenode.numlevels == 3
        assert storagenode.levels == [0.1, 0.2, 0.3]
        assert storagenode.storagearea == [0.4, 0.5, 0.6]
        assert storagenode.interpolate == Interpolation.block

    def test_create_storage_node_usetable_false(self):
        storagenode = StorageNode(**_create_storage_node_values(usetable=False))

        assert storagenode.id == "storagenode_id"
        assert storagenode.name == "storagenode_name"
        assert storagenode.manholeid == "manhole_id"
        assert storagenode.nodetype == NodeType.soakawaydrain
        assert storagenode.nodeid == "node_id"

        assert storagenode.usetable == False

        assert storagenode.bedlevel == 1.23
        assert storagenode.area == 2.34
        assert storagenode.streetlevel == 3.45
        assert storagenode.streetstoragearea == 4.56
        assert storagenode.storagetype == StorageType.closed

        assert storagenode.numlevels == None
        assert storagenode.levels == None
        assert storagenode.storagearea == None
        assert storagenode.interpolate == Interpolation.linear

    @pytest.mark.parametrize(
        "usetable, missingfield",
        [
            (True, "numlevels"),
            (True, "levels"),
            (True, "storagearea"),
            (False, "bedlevel"),
            (False, "area"),
            (False, "streetlevel"),
            (False, "streetstoragearea"),
        ],
    )
    def test_validate_required_usetable_fields(self, usetable: bool, missingfield: str):
        values = _create_required_storage_node_values(usetable)
        del values[missingfield]

        with pytest.raises(ValidationError) as error:
            StorageNode(**values)

        expected_message = (
            f"{missingfield} should be provided when useTable is {usetable}"
        )
        assert expected_message in str(error.value)


def _create_storage_node_values(usetable: bool) -> dict:
    values = _create_required_storage_node_values(usetable)
    values.update(dict(manholeid="manhole_id", nodetype="soakawayDrain"))

    if usetable:
        values.update(dict(interpolate="block"))
    else:
        values.update(dict(storagetype="closed"))

    return values


def _create_required_storage_node_values(usetable: bool) -> dict:
    values = dict(id="storagenode_id", name="storagenode_name", nodeid="node_id")

    if usetable:
        values.update(
            dict(
                usetable="true",
                numlevels="3",
                levels=["0.1", "0.2", "0.3"],
                storagearea=["0.4", "0.5", "0.6"],
            )
        )
    else:
        values.update(
            dict(
                usetable="false",
                bedlevel="1.23",
                area="2.34",
                streetlevel="3.45",
                streetstoragearea="4.56",
            )
        )

    return values
