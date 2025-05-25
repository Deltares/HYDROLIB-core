"""
Test all methods contained in the
hydrolib.core.dflowfm.ext.models.Boundary class
"""

from pathlib import Path

import pytest

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm.bc.models import ForcingModel
from hydrolib.core.dflowfm.ext.models import Boundary


def test_existing_file():
    polyline = "tests/data/input/boundary-conditions/tfl_01.pli"
    data = {
        "quantity": "waterlevelbnd",
        "locationfile": polyline,
        "forcingfile": ForcingModel(),
    }
    boundary_block = Boundary(**data)
    assert boundary_block.locationfile == DiskOnlyFileModel(Path(polyline))
    assert boundary_block.quantity == "waterlevelbnd"
    assert boundary_block.forcingfile == ForcingModel()
    assert boundary_block.bndwidth1d is None
    assert boundary_block.bndbldepth is None


def test_given_args_expected_values():
    # 1. Explicit declaration of parameters (to validate keys as they are written)
    dict_values = {
        "quantity": "42",
        "nodeid": "aNodeId",
        "locationfile": Path("aLocationFile"),
        "forcingfile": ForcingModel(),
        "bndwidth1d": 4.2,
        "bndbldepth": 2.4,
    }

    created_boundary = Boundary(**dict_values)

    # 3. Verify boundary values as expected.
    created_boundary_dict = created_boundary.dict()

    compare_data = dict(dict_values)
    expected_location_path = compare_data.pop("locationfile")

    for key, value in compare_data.items():
        assert created_boundary_dict[key] == value

    assert created_boundary_dict["locationfile"]["filepath"] == expected_location_path


def test_given_args_as_alias_expected_values():
    # 1. Explicit declaration of parameters (to validate keys as they are written)
    dict_values = {
        "quantity": "42",
        "nodeid": "aNodeId",
        "locationfile": Path("aLocationFile"),
        "forcingFile": ForcingModel(),
        "bndWidth1D": 4.2,
        "bndBlDepth": 2.4,
    }

    created_boundary = Boundary(**dict_values)
    boundary_as_dict = created_boundary.dict()
    # 3. Verify boundary values as expected.
    assert boundary_as_dict["quantity"] == dict_values["quantity"]
    assert boundary_as_dict["nodeid"] == dict_values["nodeid"]
    assert boundary_as_dict["locationfile"]["filepath"] == dict_values["locationfile"]
    assert boundary_as_dict["forcingfile"] == dict_values["forcingFile"]
    assert boundary_as_dict["bndwidth1d"] == dict_values["bndWidth1D"]
    assert boundary_as_dict["bndbldepth"] == dict_values["bndBlDepth"]


class TestValidateRootValidator:
    """
    Test class to validate the paradigms when evaluating
    check_nodeid_or_locationfile_present.
    """

    @pytest.mark.parametrize(
        "dict_values",
        [
            pytest.param(dict(), id="No entries."),
            pytest.param(dict(nodeid=None, locationfile=None), id="Entries are None."),
            pytest.param(dict(nodeid="", locationfile=""), id="Entries are Empty."),
        ],
    )
    def test_given_no_values_raises_valueerror(self, dict_values: dict):
        with pytest.raises(ValueError) as exc_mssg:
            Boundary.check_nodeid_or_locationfile_present(dict_values)

        # 3. Verify final expectations.
        expected_error_mssg = (
            "Either nodeId or locationFile fields should be specified."
        )
        assert str(exc_mssg.value) == expected_error_mssg

    @pytest.mark.parametrize(
        "dict_values",
        [
            pytest.param(dict(nodeid="aNodeId"), id="NodeId present."),
            pytest.param(
                dict(locationfile=Path("aLocationFile")),
                id="LocationFile present.",
            ),
            pytest.param(
                dict(nodeid="bNodeId", locationfile="bLocationFile"),
                id="Both present.",
            ),
        ],
    )
    def test_given_dict_values_doesnot_raise(self, dict_values: dict):
        return_values = Boundary.check_nodeid_or_locationfile_present(dict_values)
        assert dict_values == return_values


class TestValidateFromCtor:
    """
    Test class to validate the validation during default object creation.
    """

    @pytest.mark.parametrize(
        "dict_values",
        [
            pytest.param(dict(), id="No entries."),
            pytest.param(dict(nodeid=None, locationfile=None), id="Entries are None."),
            pytest.param(dict(nodeid=""), id="NodeId is empty."),
        ],
    )
    def test_given_no_values_raises_valueerror(self, dict_values: dict):
        required_values = dict(quantity="aQuantity")
        test_values = {**dict_values, **required_values}
        with pytest.raises(ValueError) as exc_mssg:
            Boundary(**test_values)

        # 3. Verify final expectations.
        expected_error_mssg = (
            "Either nodeId or locationFile fields should be specified."
        )
        assert expected_error_mssg in str(exc_mssg.value)

    @pytest.mark.parametrize(
        "dict_values",
        [
            pytest.param(dict(nodeid="aNodeId"), id="NodeId present."),
            pytest.param(
                dict(locationfile=Path("aLocationFile")),
                id="LocationFile present.",
            ),
            pytest.param(
                dict(nodeid="bNodeId", locationfile=Path("bLocationFile")),
                id="Both present.",
            ),
        ],
    )
    def test_given_dict_values_doesnot_raise(self, dict_values: dict):
        required_values = dict(quantity="aQuantity", forcingfile=ForcingModel())
        test_values = {**dict_values, **required_values}
        created_boundary = Boundary(**test_values)

        expected_locationfile = test_values.pop("locationfile", None)

        for key, value in test_values.items():
            if key == "forcing_file":
                value = value.dict()
            assert created_boundary.dict()[key] == value

        assert (
            created_boundary.dict()["locationfile"]["filepath"] == expected_locationfile
        )
