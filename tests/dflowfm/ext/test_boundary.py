"""
Test all methods contained in the
hydrolib.core.dflowfm.ext.models.Boundary class
"""

from pathlib import Path

import pytest

from hydrolib.core.base.models import DiskOnlyFileModel
from hydrolib.core.dflowfm import Operand
from hydrolib.core.dflowfm.bc.models import ForcingModel
from hydrolib.core.dflowfm.ext.models import Boundary, ExtModel
from hydrolib.tools.extforce_convert.utils import construct_filemodel_new_or_existing


def test_existing_file():
    """Test creation of Boundary with an existing file and default values."""
    polyline = "tests/data/input/boundary-conditions/tfl_01.pli"
    data = {
        "quantity": "waterlevelbnd",
        "locationfile": polyline,
        "forcingfile": ForcingModel(),
    }
    boundary_block = Boundary(**data)
    assert boundary_block.locationfile == DiskOnlyFileModel(Path(polyline))
    assert boundary_block.quantity == "waterlevelbnd"
    assert boundary_block.forcingfile == data["forcingfile"]
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
    created_boundary_dict = created_boundary.model_dump()

    compare_data = dict(dict_values)
    expected_location_path = compare_data.pop("locationfile")
    compare_data.pop("forcingfile")

    for key, value in compare_data.items():
        assert created_boundary_dict[key] == value

    assert created_boundary.forcingfile == dict_values["forcingfile"]
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
        "operand": "maximum"
    }

    created_boundary = Boundary(**dict_values)
    boundary_as_dict = created_boundary.model_dump()
    # 3. Verify boundary values as expected.
    assert boundary_as_dict["quantity"] == dict_values["quantity"]
    assert boundary_as_dict["nodeid"] == dict_values["nodeid"]
    assert boundary_as_dict["locationfile"]["filepath"] == dict_values["locationfile"]
    assert created_boundary.forcingfile == dict_values["forcingFile"]
    assert boundary_as_dict["bndwidth1d"] == dict_values["bndWidth1D"]
    assert boundary_as_dict["bndbldepth"] == dict_values["bndBlDepth"]
    assert boundary_as_dict["operand"] == dict_values["operand"]

def test_return_time_field_is_renamed():
    dict_values = {
        "quantity": "42",
        "nodeid": "aNodeId",
        "locationfile": Path("aLocationFile"),
        "forcingfile": ForcingModel(),
        "return_time": 10.0,
    }

    created_boundary = Boundary(**dict_values)
    assert created_boundary.returntime == dict_values["return_time"]


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
        required_values = dict(quantity="aQuantity", forcingfile=ForcingModel())
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
        test_values.pop("forcingfile", None)

        for key, value in test_values.items():
            assert created_boundary.model_dump()[key] == value

        assert (
            created_boundary.model_dump()["locationfile"]["filepath"]
            == expected_locationfile
        )


_LEGACY_OPERAND_CASES = [
    pytest.param("O", Operand.override, id="O->override"),
    pytest.param("A", Operand.override_if_missing, id="A->overrideIfMissing"),
    pytest.param("+", Operand.add, id="+->add"),
    pytest.param("*", Operand.multiply, id="*->multiply"),
    pytest.param("X", Operand.maximum, id="X->maximum"),
    pytest.param("N", Operand.minimum, id="N->minimum"),
]

class TestBoundaryLegacyOperandConversion:
    """Tests that legacy single-character OPERAND values in old .ext files
    are correctly converted to modern Operand enum values when loading."""

    @pytest.mark.parametrize("legacy_operand, expected_operand", _LEGACY_OPERAND_CASES)
    def test_legacy_operand_in_file_is_converted_correctly(
            self,
            legacy_operand: str,
            expected_operand: Operand,
    ):
        """Instantiating a Boundary with a legacy OPERAND value yields the correct modern Operand."""
        dict_values = {
            "quantity": "42",
            "nodeid": "aNodeId",
            "locationfile": Path("aLocationFile"),
            "forcingfile": ForcingModel(),
            "bndwidth1d": 4.2,
            "bndbldepth": 2.4,
            "operand": legacy_operand
        }

        created_boundary = Boundary(**dict_values)
        assert created_boundary.operand == expected_operand


_BC_CONTENT = (
    "[Forcing]\n"
    "name              = L1_0001\n"
    "function          = timeseries\n"
    "timeInterpolation = linear\n"
    "quantity          = time\n"
    "unit              = minutes since 2015-01-01 00:00:00\n"
    "quantity          = waterlevelbnd\n"
    "unit              = m\n"
    "0.0   0.01\n"
    "120.0 0.01\n"
)

_EXT_CONTENT = (
    "[Boundary]\n"
    "quantity     = waterlevelbnd\n"
    "locationFile = bnd.pli\n"
    "forcingFile  = bnd.bc\n"
)


def _write_boundary_ext_tree(directory: Path) -> Path:
    """Write a new-style ext file referencing a real .bc forcing file.

    Args:
        directory: Directory in which to create ``new.ext``, ``bnd.bc`` and ``bnd.pli``.

    Returns:
        Path: The path to the written ``new.ext`` file.
    """
    (directory / "bnd.bc").write_text(_BC_CONTENT, encoding="utf8")
    (directory / "bnd.pli").write_text("bnd\n2 2\n0 0\n0 1\n", encoding="utf8")
    ext_path = directory / "new.ext"
    ext_path.write_text(_EXT_CONTENT, encoding="utf8")
    return ext_path


class TestBoundaryForcingFileNonRecursiveLoad:
    """Regression tests for the ``recurse=False`` load / ``recurse=True`` save round-trip.

    When an ``ExtModel`` is loaded non-recursively (as the external-forcings converter
    does), the ``.bc`` forcing file referenced by a ``[Boundary]`` block must not be
    parsed into an (empty) ``ForcingModel``. It must instead be held as a
    ``DiskOnlyFileModel`` placeholder, so that a subsequent ``save(recurse=True)`` leaves
    the real ``.bc`` file untouched instead of overwriting it with empty content.
    """

    def test_forcingfile_is_disk_only_when_loaded_non_recursively(self, tmp_path: Path):
        """Test that a non-recursive load keeps the forcing file as a DiskOnlyFileModel.

        Test scenario:
            Loading an ext file with ``recurse=False`` must resolve ``forcingFile`` to a
            ``DiskOnlyFileModel`` (the on-disk-but-not-parsed placeholder), NOT an empty
            ``ForcingModel``.
        """
        ext_path = _write_boundary_ext_tree(tmp_path)

        model = ExtModel(filepath=ext_path, recurse=False)

        forcingfile = model.boundary[0].forcingfile
        assert isinstance(forcingfile, DiskOnlyFileModel), (
            f"Expected DiskOnlyFileModel under recurse=False, got {type(forcingfile).__name__}"
        )

    def test_forcingfile_is_forcingmodel_when_loaded_recursively(self, tmp_path: Path):
        """Test that a recursive load parses the forcing file into a ForcingModel.

        Test scenario:
            Loading the same ext file with ``recurse=True`` fully parses ``forcingFile``
            into a ``ForcingModel`` carrying the forcing blocks.
        """
        ext_path = _write_boundary_ext_tree(tmp_path)

        model = ExtModel(filepath=ext_path, recurse=True)

        forcingfile = model.boundary[0].forcingfile
        assert isinstance(forcingfile, ForcingModel), (
            f"Expected ForcingModel under recurse=True, got {type(forcingfile).__name__}"
        )
        assert len(forcingfile.forcing) == 1, (
            f"Expected 1 forcing block parsed, got {len(forcingfile.forcing)}"
        )

    def test_save_recurse_does_not_empty_unloaded_bc_file(self, tmp_path: Path):
        """Test that saving recursively does not clobber a non-recursively loaded .bc file.

        Test scenario:
            Load the ext file with ``recurse=False`` (leaving ``.bc`` unparsed), then
            ``save(recurse=True)``. The referenced ``bnd.bc`` must retain its original
            content rather than being overwritten with an empty forcing file.
        """
        ext_path = _write_boundary_ext_tree(tmp_path)
        bc_path = tmp_path / "bnd.bc"
        original_bc = bc_path.read_text(encoding="utf8")

        model = ExtModel(filepath=ext_path, recurse=False)
        model.save(recurse=True, exclude_unset=True)

        assert bc_path.read_text(encoding="utf8") == original_bc, (
            "The .bc forcing file was rewritten by save(recurse=True); it should have been "
            "left untouched because it was never loaded."
        )

    def test_save_preserves_forcingfile_reference_after_nonrecursive_load(
        self, tmp_path: Path
    ):
        """Test that saving preserves the ``forcingFile`` reference in the [Boundary] block.

        Test scenario:
            After a ``recurse=False`` load (where ``forcingFile`` is a ``DiskOnlyFileModel``
            placeholder), saving must still write ``forcingFile = bnd.bc`` into the ext block,
            and reloading the saved file must recover the same reference.
        """
        ext_path = _write_boundary_ext_tree(tmp_path)
        out_path = tmp_path / "out.ext"

        model = ExtModel(filepath=ext_path, recurse=False)
        model.save(filepath=out_path, recurse=True, exclude_unset=True)

        saved_text = out_path.read_text(encoding="utf8")
        assert "forcingFile" in saved_text, (
            f"Saved ext block lost the forcingFile keyword:\n{saved_text}"
        )
        assert "bnd.bc" in saved_text, (
            f"Saved ext block lost the .bc reference:\n{saved_text}"
        )

        reloaded = ExtModel(filepath=out_path, recurse=False)
        assert str(reloaded.boundary[0].forcingfile.filepath) == "bnd.bc", (
            f"Reloaded forcingFile reference changed: {reloaded.boundary[0].forcingfile.filepath}"
        )

    def test_forcing_property_returns_none_for_disk_only_placeholder(self, tmp_path: Path):
        """Test that the ``forcing`` property returns None for an unparsed placeholder.

        Test scenario:
            When ``forcingfile`` is a ``DiskOnlyFileModel`` (non-recursive load), the
            ``Boundary.forcing`` property must return ``None`` rather than raise
            ``AttributeError``.
        """
        ext_path = _write_boundary_ext_tree(tmp_path)

        model = ExtModel(filepath=ext_path, recurse=False)
        boundary = model.boundary[0]

        assert isinstance(boundary.forcingfile, DiskOnlyFileModel), (
            f"Expected DiskOnlyFileModel, got {type(boundary.forcingfile).__name__}"
        )
        assert boundary.forcing is None, (
            f"Expected forcing property to be None for a placeholder, got {boundary.forcing!r}"
        )

    def test_converter_load_pattern_does_not_empty_bc(self, tmp_path: Path):
        """Test the converter's exact load pattern does not empty an existing .bc file.

        Test scenario:
            Reproduces issue #1143 at the mechanism level: the external-forcings converter
            loads a pre-existing new-style ext file via
            ``construct_filemodel_new_or_existing(ExtModel, path, recurse=False)``
            (``main_converter`` line 128) and later saves with ``recurse=True``. The
            referenced ``.bc`` file must survive intact.
        """
        ext_path = _write_boundary_ext_tree(tmp_path)
        bc_path = tmp_path / "bnd.bc"
        original_bc = bc_path.read_text(encoding="utf8")

        model = construct_filemodel_new_or_existing(ExtModel, ext_path, recurse=False)
        model.save(recurse=True, exclude_unset=True)

        assert bc_path.read_text(encoding="utf8") == original_bc, (
            "The converter load pattern (recurse=False) followed by save(recurse=True) "
            "emptied the existing .bc file (issue #1143)."
        )
