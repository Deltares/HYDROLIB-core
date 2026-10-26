"""End-to-end test of #978: the `extforce_convert` CLI keeps every quantity of a shared `.bc`."""

import shutil
from pathlib import Path

import pytest

from hydrolib.core.dflowfm.bc.models import ForcingModel
from hydrolib.tools.extforce_convert.cli import main

pytestmark = pytest.mark.e2e


def test_cli_conversion_keeps_every_quantity_of_a_shared_bc(
    tmp_path: Path, input_files_dir: Path
):
    """Convert the `shared-bc-file` model with `--mdufile`, as a user would.

    Input: `tracerbndIM1` and `tracerbndIM2` on `Slib_Noord.pli`, `tracerbndIM1` alone on
    `Slib_Oost.pli`.
    Before the fix: `Slib_Noord.bc` held only `tracerbndIM2`.
    Expected: both quantities (two blocks each) in `Slib_Noord.bc`, the other file unchanged,
    and the new ext written next to the MDU.
    """
    model_dir = tmp_path / "shared-bc-file"
    shutil.copytree(input_files_dir / "shared-bc-file", model_dir)

    main(["--mdufile", str(model_dir / "model.mdu")])

    shared = ForcingModel(model_dir / "Slib_Noord.bc")
    quantities = sorted(
        pair.quantity
        for forcing in shared.forcing
        for pair in forcing.quantityunitpair
        if pair.quantity != "time"
    )
    assert quantities == [
        "tracerbndIM1",
        "tracerbndIM1",
        "tracerbndIM2",
        "tracerbndIM2",
    ]
    assert len(ForcingModel(model_dir / "Slib_Oost.bc").forcing) == 2
    assert (model_dir / "new.ext").is_file()
