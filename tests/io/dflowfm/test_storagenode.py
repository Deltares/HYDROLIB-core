import pytest
from pydantic.error_wrappers import ValidationError

from hydrolibcore.io.dflowfm.storagenode.models import (
    Interpolation,
    NodeType,
    StorageNode,
    StorageNodeGeneral,
    StorageNodeModel,
    StorageType,
)


class TestStorageNodeGeneral:
    def test_create(self):
        general = StorageNodeGeneral()

        assert general.fileversion == "2.00"
        assert general.filetype == "storageNodes"
        assert general.usestreetstorage == True


class TestStorageNode:
    def test_create_storage_node_usetable_true(self):
        storagenode = StorageNode(**_create_storage_node_values(usetable=True))

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
            (False, "bedlevel"),
            (False, "area"),
            (False, "streetlevel"),
        ],
    )
    def test_validate_required_usetable_fields(self, usetable: bool, missingfield: str):
        values = _create_required_storage_node_values(usetable)
        del values[missingfield]

        with pytest.raises(ValidationError) as error:
            StorageNode(**values)

        expected_message = (
            f"{missingfield} should be provided when usetable is {usetable}"
        )
        assert expected_message in str(error.value)

    @pytest.mark.parametrize("missingfield", ["levels", "storagearea"])
    def test_validate_required_lists_numlevels(self, missingfield: str):
        values = _create_required_storage_node_values(usetable=True)
        del values[missingfield]

        with pytest.raises(ValidationError) as error:
            StorageNode(**values)

        expected_message = (
            f"List {missingfield} cannot be missing if numlevels is given."
        )
        assert expected_message in str(error.value)

    @pytest.mark.parametrize("field", ["storagearea", "levels"])
    def test_validate_numlevels_fields_lengths(self, field: str):
        values = _create_required_storage_node_values(True)
        values[field] = [1, 2, 3, 4, 5, 6, 7]

        with pytest.raises(ValidationError) as error:
            StorageNode(**values)

        expected_message = (
            f"Number of values for {field} should be equal to the numlevels value."
        )
        assert expected_message in str(error.value)


class TestStorageNodeModel:
    def test_validate_storagenode_requires_streetstoragearea(self):

        storagenodevalues = _create_required_storage_node_values(False)
        del storagenodevalues["streetstoragearea"]

        with pytest.raises(ValidationError) as error:
            StorageNodeModel(**dict(storagenode=[storagenodevalues]))

        expected_message = f"streetStorageArea should be provided when useStreetStorage is True and useTable is False for storage node with id storagenode_id"
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
                levels="0.1 0.2 0.3",
                storagearea="0.4 0.5 0.6",
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
