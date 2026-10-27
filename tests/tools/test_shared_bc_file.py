"""Regression tests for #978: quantities sharing a polyline must share one `.bc` file."""

import shutil
from pathlib import Path
from typing import List

import pytest

from hydrolib.core.dflowfm.bc.models import ForcingModel
from hydrolib.tools.extforce_convert.main_converter import ExternalForcingConverter

pytestmark = pytest.mark.integration

SHARED_BC_MODEL = "shared-bc-file"

MDU_TEXT = """[General]
fileVersion = 1.09
fileType = modelDef

[time]
RefDate = 20111222
Tunit = M
DtUser = 600.
Startdatetime = 20161222000000
Stopdatetime = 20180101000000

[physics]
Salinity = 1
Temperature = 5

[external forcing]
ExtForceFile = old.ext
ExtForceFileNew = new.ext
"""

PLI_TEXT = "NS_N\n2  2\n4.0 53.9\n7.3 53.9\n"
PLIZ_TEXT = "L1\n 2 3\n 63.35 12.95 -4.2\n 45.20 6.35 -3.0\n"
POL_TEXT = "L1\n3 2\n47982.99 419580.34\n47545.80 419245.15\n47647.81 419121.28\n"
TIM_1_COLUMN = "1592640.0 1.5\n1637280.0 1.6\n"
TIM_3_COLUMNS = "0.0 1.0 2.0 3.0\n100 1.0 2.0 3.0\n"

EXISTING_BC_TEXT = """[General]
fileVersion = 1.01
fileType    = boundConds

[Forcing]
name              = NS_N_0001
function          = timeseries
timeInterpolation = linear
quantity          = time
unit              = MINUTES SINCE 2011-12-22 00:00:00
quantity          = tracerbndIM1
unit              = -
1592640.0  1.0
1637280.0  1.1
"""

EXISTING_NEW_EXT_TEXT = """[General]
fileVersion = 3.00
fileType    = extForce

[Boundary]
quantity     = tracerbndIM1
locationFile = Slib_Noord.pli
forcingFile  = Slib_Noord.bc
"""


def _old_block(quantity: str, filename: str, filetype: int, method: int, extra: str = "") -> str:
    """Return one old-style external forcing entry, ended by the blank line that separates entries."""
    return (
        f"QUANTITY={quantity}\nFILENAME={filename}\nFILETYPE={filetype}\n"
        f"METHOD={method}\nOPERAND=O\n{extra}\n"
    )


def _convert(
    model_dir: Path,
    old_ext: str,
    files: dict[str, str],
    new_ext: str | None = None,
    new_ext_name: str = "new.ext",
) -> Path:
    """Write a model made of `files`, convert it, and return the model directory.

    `new_ext_name` is the path of the new external forcing file relative to the MDU.
    """
    model_dir.mkdir(parents=True)
    for name, text in files.items():
        (model_dir / name).write_text(text)
    (model_dir / "old.ext").write_text(old_ext)
    (model_dir / "model.mdu").write_text(
        MDU_TEXT.replace("ExtForceFileNew = new.ext", f"ExtForceFileNew = {new_ext_name}")
    )
    if new_ext is not None:
        (model_dir / new_ext_name).parent.mkdir(parents=True, exist_ok=True)
        (model_dir / new_ext_name).write_text(new_ext)

    converter = ExternalForcingConverter.from_mdu(model_dir / "model.mdu")
    converter.update()
    converter.save()

    return model_dir


def _bc_quantities(bc_file: Path) -> List[str]:
    """Return the non-time quantity of every `[Forcing]` block of a `.bc` file, in file order."""
    forcing_model = ForcingModel(bc_file)
    return [
        quantity_unit_pair.quantity
        for forcing in forcing_model.forcing
        for quantity_unit_pair in forcing.quantityunitpair
        if quantity_unit_pair.quantity != "time"
    ]


@pytest.fixture
def converter(tmp_path: Path, input_files_dir: Path) -> ExternalForcingConverter:
    """Return a converter, already updated, for a private copy of the `shared-bc-file` model.

    `old.ext` holds `tracerbndIM1` and `tracerbndIM2` on `Slib_Noord.pli`, and `tracerbndIM1`
    alone on `Slib_Oost.pli`.
    """
    model_dir = tmp_path / SHARED_BC_MODEL
    shutil.copytree(input_files_dir / SHARED_BC_MODEL, model_dir)

    converter = ExternalForcingConverter.from_mdu(model_dir / "model.mdu")
    converter.update()

    return converter


@pytest.fixture
def converted_model_dir(tmp_path: Path, input_files_dir: Path) -> Path:
    """Convert a private copy of the `shared-bc-file` model and return its directory."""
    model_dir = tmp_path / SHARED_BC_MODEL
    shutil.copytree(input_files_dir / SHARED_BC_MODEL, model_dir)

    converter = ExternalForcingConverter.from_mdu(model_dir / "model.mdu")
    converter.update()
    converter.save()

    return model_dir


class TestQuantitiesSharingPolyline:
    """Case 1 of #978: two boundary quantities on one polyline.

    The `shared-bc-file` model has `tracerbndIM1` and `tracerbndIM2` on `Slib_Noord.pli`, and
    `tracerbndIM1` alone on `Slib_Oost.pli`. Each quantity is converted to its own
    `ForcingModel` named `Slib_Noord.bc`, and each model is saved with the file opened in `"w"`
    mode.
    """

    def test_shared_polyline_keeps_every_quantity(self, converted_model_dir: Path):
        """Both quantities of `Slib_Noord.pli` are written to `Slib_Noord.bc`.

        Input: `tracerbndIM1` and `tracerbndIM2` on the same `.pli`, two `.tim` points each.
        Before the fix: the second quantity overwrote the first and only `tracerbndIM2` was
        left, which makes the kernel fail with "No signals for polyline ... and quantity
        TRACERBNDIM1".
        Expected: 4 blocks, two per quantity, in one file.
        """
        quantities = _bc_quantities(converted_model_dir / "Slib_Noord.bc")

        assert sorted(quantities) == [
            "tracerbndIM1",
            "tracerbndIM1",
            "tracerbndIM2",
            "tracerbndIM2",
        ]

    def test_single_quantity_polyline_is_unchanged(self, converted_model_dir: Path):
        """Control: a polyline used by one quantity keeps its own `.bc`, unaffected by sharing.

        Input: `tracerbndIM1` alone on `Slib_Oost.pli`.
        Expected: 2 blocks (one per `.tim` point), both `tracerbndIM1`.
        """
        quantities = _bc_quantities(converted_model_dir / "Slib_Oost.bc")

        assert quantities == ["tracerbndIM1", "tracerbndIM1"]

    def test_new_ext_points_both_boundaries_to_the_shared_bc(
        self, converted_model_dir: Path
    ):
        """Sharing the model must not change which file each `[Boundary]` points to.

        Expected: both `tracerbndIM1` and `tracerbndIM2` reference `Slib_Noord.bc` in `new.ext`.
        """
        text = (converted_model_dir / "new.ext").read_text()

        assert text.count("forcingFile  = Slib_Noord.bc") == 2

    def test_updating_twice_does_not_duplicate_blocks(
        self, converter: ExternalForcingConverter
    ):
        """Converting the same old ext again on one converter must not add the blocks again.

        The second `update()` finds the first run's blocks already in the ext model and merges
        into them, skipping the forcings they hold.
        Expected: still 4 blocks in `Slib_Noord.bc`.
        """
        bc_file = converter.ext_model.filepath.parent / "Slib_Noord.bc"

        converter.update()
        converter.save()

        assert len(_bc_quantities(bc_file)) == 4

    def test_saving_twice_is_idempotent(self, converter: ExternalForcingConverter):
        """A second save rewrites the `.bc` files instead of appending to them.

        This is what rules out a plain "append mode" fix (the first attempt on this issue):
        saving twice would then duplicate every block.
        Expected: the file is byte-identical after the second save, and still holds 4 blocks.
        """
        bc_file = converter.ext_model.filepath.parent / "Slib_Noord.bc"

        converter.save()
        first_save = bc_file.read_text()
        converter.save()
        second_save = bc_file.read_text()

        assert second_save == first_save
        assert len(_bc_quantities(bc_file)) == 4


class TestBlocksSharingBcFile:
    """Any two converted blocks that write the same `.bc` must end up in it, once.

    The cause is the same as in `TestQuantitiesSharingPolyline`: every block gets its own
    `ForcingModel` named after its input file, so two blocks with the same input write one
    path twice. These tests cover the other block types, cross-type pairs, and an existing
    new external forcing file. The tests named `..._are_not_duplicated` and
    `..._written_once` are guards: they pass without any fix (the identical data is simply
    written twice), and they must keep passing so that merging never produces duplicates.
    """

    def test_spatial_quantities_sharing_a_tim_file(self, tmp_path: Path):
        """Case 2: two spatial quantities that read the same uniform `.tim`.

        Input: `windx` and `windy`, both `FILETYPE=1`, on `wind.tim` (a single data column).
        Before the fix: both `[Spatial]` blocks wrote `wind.bc`; only `windy` was left.
        Expected: `wind.bc` holds `windx` and `windy`.
        """
        old_ext = _old_block("windx", "wind.tim", 1, 1) + _old_block("windy", "wind.tim", 1, 1)

        model_dir = _convert(tmp_path / "m", old_ext, {"wind.tim": TIM_1_COLUMN})

        assert sorted(_bc_quantities(model_dir / "wind.bc")) == ["windx", "windy"]

    def test_boundary_and_sourcesink_sharing_a_polyline(self, tmp_path: Path):
        """Case 3: blocks of different types that resolve to the same `.bc`.

        Input: `salinitybnd` and `discharge_salinity_temperature_sorsin` on `leftsor.pliz`.
        The boundary has one `.tim` per polyline point, the source/sink a single 3-column
        `leftsor.tim`.
        Before the fix: the block type saved later won, so `leftsor.bc` held only the three
        `sourcesink_*` blocks while `new.ext` still had a `[Boundary]` pointing at it.
        Expected: 2 `salinitybnd` blocks plus `sourcesink_discharge`, `_salinity` and
        `_temperature`. The kernel matches blocks by (name, quantity), so they coexist.
        """
        old_ext = _old_block("salinitybnd", "leftsor.pliz", 9, 1) + _old_block(
            "discharge_salinity_temperature_sorsin", "leftsor.pliz", 9, 1, "AREA=1.0\n"
        )
        files = {
            "leftsor.pliz": PLIZ_TEXT,
            "leftsor.tim": TIM_3_COLUMNS,
            # the boundary reads one series per polyline point
            "leftsor_0001.tim": "0.0 31.0\n100 32.0\n",
            "leftsor_0002.tim": "0.0 33.0\n100 34.0\n",
        }

        model_dir = _convert(tmp_path / "m", old_ext, files)

        assert sorted(_bc_quantities(model_dir / "leftsor.bc")) == [
            "salinitybnd",
            "salinitybnd",
            "sourcesink_discharge",
            "sourcesink_salinity",
            "sourcesink_temperature",
        ]

    def test_sourcesinks_sharing_a_polyline_are_not_duplicated(self, tmp_path: Path):
        """Guard: two source/sinks on one polyline hold identical forcings.

        Input: the same `sorsin` twice on `leftsor.pliz`, with `AREA=1.0` and `AREA=2.0`
        (same `id`, so the same forcing blocks).
        Nothing was lost before the fix, because both models hold the same data. A merge that
        simply appended would give 6 blocks.
        Expected: exactly one set of 3 blocks.
        """
        old_ext = _old_block(
            "discharge_salinity_temperature_sorsin", "leftsor.pliz", 9, 1, "AREA=1.0\n"
        ) + _old_block(
            "discharge_salinity_temperature_sorsin", "leftsor.pliz", 9, 1, "AREA=2.0\n"
        )
        files = {"leftsor.pliz": PLIZ_TEXT, "leftsor.tim": TIM_3_COLUMNS}

        model_dir = _convert(tmp_path / "m", old_ext, files)

        assert sorted(_bc_quantities(model_dir / "leftsor.bc")) == [
            "sourcesink_discharge",
            "sourcesink_salinity",
            "sourcesink_temperature",
        ]

    def test_laterals_sharing_a_polygon_are_not_duplicated(self, tmp_path: Path):
        """Guard: a 1d and a 2d lateral on one polygon read the same discharge series.

        Input: `lateraldischarge1d` and `lateraldischarge2d` on `afstroming.pol`. Both blocks
        get the same `id` and the same `discharge` forcing, and point at `afstroming.bc`.
        Expected: a single `discharge` block, not two identical ones.
        """
        old_ext = _old_block("lateraldischarge1d", "afstroming.pol", 10, 3) + _old_block(
            "lateraldischarge2d", "afstroming.pol", 10, 3
        )
        files = {"afstroming.pol": POL_TEXT, "afstroming.tim": "0 1.0\n60 2.0\n"}

        model_dir = _convert(tmp_path / "m", old_ext, files)

        assert _bc_quantities(model_dir / "afstroming.bc") == ["discharge"]

    def test_identical_entries_are_written_once(self, tmp_path: Path):
        """Guard: an entry listed twice must not be written twice.

        Input: `salinitybnd` twice on one polyline, as in the test-bench model
        `f019_transport/c080_1Dchannel_explicit_horizontal_dispersion/salinity.ext`.
        `main` writes one block here; a naive merge (the first version of this fix) wrote two
        identical ones. The kernel ignores the second, but the output should not change.
        Expected: one `salinitybnd` block.
        """
        old_ext = _old_block("salinitybnd", "Slib_Noord.pli", 9, 3) * 2
        files = {"Slib_Noord.pli": PLI_TEXT, "Slib_Noord_0001.tim": TIM_1_COLUMN}

        model_dir = _convert(tmp_path / "m", old_ext, files)

        assert _bc_quantities(model_dir / "Slib_Noord.bc") == ["salinitybnd"]

    def test_three_quantities_on_one_polyline_are_all_kept(self, tmp_path: Path):
        """Each block merges into the one before it, so a chain of three keeps all three.

        Input: `tracerbndIM1`, `tracerbndIM2` and `tracerbndIM3` on one polyline.
        Before the fix: only the last quantity (`tracerbndIM3`) was left.
        Expected: one block per quantity.
        """
        old_ext = "".join(
            _old_block(f"tracerbndIM{i}", "Slib_Noord.pli", 9, 3) for i in (1, 2, 3)
        )
        files = {"Slib_Noord.pli": PLI_TEXT, "Slib_Noord_0001.tim": TIM_1_COLUMN}

        model_dir = _convert(tmp_path / "m", old_ext, files)

        assert _bc_quantities(model_dir / "Slib_Noord.bc") == [
            "tracerbndIM1",
            "tracerbndIM2",
            "tracerbndIM3",
        ]

    def test_new_ext_in_a_subfolder_of_the_mdu_keeps_every_quantity(
        self, tmp_path: Path
    ):
        """Case 5: the new ext is not in the MDU folder (`ExtForceFileNew = sub/new.ext`).

        Input: `tracerbndIM1` and `tracerbndIM2` on `Slib_Noord.pli`, which is next to the MDU.
        The converter writes the `.bc` next to the new ext, so `sub/Slib_Noord.bc`.
        Expected: both quantities in that file, and both `[Boundary]` blocks reference it.
        The `locationFile` written into `sub/new.ext` is not checked here: it is the converter's
        own path handling and does not depend on the shared `.bc`.
        """
        old_ext = _old_block("tracerbndIM1", "Slib_Noord.pli", 9, 3) + _old_block(
            "tracerbndIM2", "Slib_Noord.pli", 9, 3
        )
        files = {"Slib_Noord.pli": PLI_TEXT, "Slib_Noord_0001.tim": TIM_1_COLUMN}

        model_dir = _convert(
            tmp_path / "m", old_ext, files, new_ext_name="sub/new.ext"
        )

        assert _bc_quantities(model_dir / "sub" / "Slib_Noord.bc") == [
            "tracerbndIM1",
            "tracerbndIM2",
        ]
        new_ext_text = (model_dir / "sub" / "new.ext").read_text()
        assert new_ext_text.count("forcingFile  = Slib_Noord.bc") == 2

    def test_quantity_is_added_to_a_bc_of_the_existing_new_ext(self, tmp_path: Path):
        """Case 4: appending to a `.bc` that the existing new ext already references.

        Input: `new.ext` already has `[Boundary] tracerbndIM1 -> Slib_Noord.bc`, `Slib_Noord.bc`
        exists with that block, and the old ext adds `tracerbndIM2` on the same polyline.
        Before the fix: the existing new ext is loaded without its child files, so the existing
        boundary held a `DiskOnlyFileModel` placeholder; the new model overwrote the file and
        `tracerbndIM1` was lost while `new.ext` still pointed at it.
        Expected: the existing `.bc` is parsed and merged into, so both quantities are present.
        """
        old_ext = _old_block("tracerbndIM2", "Slib_Noord.pli", 9, 3)
        files = {
            "Slib_Noord.pli": PLI_TEXT,
            "Slib_Noord_0001.tim": TIM_1_COLUMN,
            "Slib_Noord.bc": EXISTING_BC_TEXT,
        }

        model_dir = _convert(tmp_path / "m", old_ext, files, EXISTING_NEW_EXT_TEXT)

        assert sorted(_bc_quantities(model_dir / "Slib_Noord.bc")) == [
            "tracerbndIM1",
            "tracerbndIM2",
        ]

    def test_existing_new_ext_boundary_without_bc_on_disk_is_kept(self, tmp_path: Path):
        """Case 4b: the `.bc` named by the existing new ext does not exist on disk.

        Input: as in case 4 but without `Slib_Noord.bc`. There is nothing to merge into.
        Expected: the file is created with only `tracerbndIM2`, and the existing `[Boundary]`
        for `tracerbndIM1` stays in `new.ext` (it must not be reset or dropped).
        """
        old_ext = _old_block("tracerbndIM2", "Slib_Noord.pli", 9, 3)
        files = {"Slib_Noord.pli": PLI_TEXT, "Slib_Noord_0001.tim": TIM_1_COLUMN}

        model_dir = _convert(tmp_path / "m", old_ext, files, EXISTING_NEW_EXT_TEXT)

        new_ext_text = (model_dir / "new.ext").read_text()
        assert new_ext_text.count("forcingFile  = Slib_Noord.bc") == 2
        assert _bc_quantities(model_dir / "Slib_Noord.bc") == ["tracerbndIM2"]

