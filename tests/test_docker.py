from pathlib import Path

import pytest
from devtools import debug

from hydrolib.core.dflowfm.mdu.models import FMModel
from hydrolib.core.dflowfm.structure.models import (
    FlowDirection,
    StructureModel,
    Weir,
)
from hydrolib.core.dimr.models import DIMR, FMComponent, Start
from tests.utils import test_input_dir, test_output_dir

from .utils import test_output_dir


def test_from_scratch_docker():
    # TODO Make a valid model from scratch
    dimr = DIMR()
    fm = FMModel()
    fm.filepath = Path("test.mdu")
    # debug(fm.geometry.netfile)
    # manipulate the model
    # Start adding geometry
    # fm.geometry.netfile.network.mesh1d_add_branch()

    # Add some structures, note this is invalid because it doesn't
    # have a branch or coordinates yet, but it will work for demo purposes
    # Note: either branchid + chainage or coordinates are mandatory for the structures.
    struc = Weir(
        allowedflowdir=FlowDirection.none,
        crestlevel=0.0,
        branchid="aBranchId",
        chainage=4.2,
    )
    struc.comments.crestlevel = "This is a comment"
    fm.geometry.structurefile = [StructureModel(structure=[struc])]

    # add FM as DIMR component and save to *folder*
    dimr.component.append(
        FMComponent(name="test", workingDir=".", inputfile=fm.filepath, model=fm)
    )
    dimr.control.append(Start(name="test"))
    output_dir = test_output_dir / "docker"

    save_path = test_output_dir / "docker" / "dimr_config.xml"
    dimr.save(filepath=save_path, recurse=True)
    assert (output_dir / "network.nc").is_file()
    assert (output_dir / "test.mdu").is_file()
    assert (output_dir / "structures.ini").is_file()
    assert save_path.is_file()


@pytest.mark.docker
def test_existing_model_saved_docker():

    test_file = (
        test_input_dir
        / "e02"
        / "f101_1D-boundaries"
        / "c01_steady-state-flow"
        / "dimr_config.xml"
    )

    dimr = DIMR(filepath=test_file)

    output_dir = test_output_dir / "docker"
    save_path = output_dir / "dimr_config.xml"

    dimr.save(filepath=save_path, recurse=True)
    assert (output_dir / "Boundary_net.nc").is_file()
    assert (output_dir / "Boundary.mdu").is_file()
    assert (output_dir / "ObservationPoints.ini").is_file()
    # assert (output_dir / "ObservationPoints_crs.ini").is_file() # Only possible once issue #159 is done
    assert (output_dir / "Boundary.ext").is_file()
    assert (output_dir / "BoundaryConditions.bc").is_file()
    assert (output_dir / "CrossSectionLocations.ini").is_file()
    assert (output_dir / "CrossSectionDefinitions.ini").is_file()
    assert (output_dir / "roughness-Main.ini").is_file()
    assert save_path.is_file()
