from devtools import debug
import pytest

from hydrolib.core.io.dimr.models import DIMR, FMComponent
from hydrolib.core.io.mdu.models import FMModel
from hydrolib.core.io.net.models import NetworkModel
from hydrolib.core.io.structure.models import FlowDirection, StructureModel, Weir
from tests.utils import test_input_dir, test_output_dir

from ..utils import test_output_dir


@pytest.mark.skip  # skipped as long as its imcomplete
def test_from_scratch_docker():
    # TODO Make a valid model from scratch
    dimr = DIMR()
    fm = FMModel()
    fm.filepath = "test.mdu"
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
    dimr.save(folder=test_output_dir / "docker")
    assert (test_output_dir / "docker" / "network.nc").is_file()
    assert (test_output_dir / "docker" / "test.mdu").is_file()
    assert (test_output_dir / "docker" / "structures.ini").is_file()
    assert (test_output_dir / "docker" / "dimr_config.xml").is_file()


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
    dimr.save(folder=test_output_dir / "docker")
    assert (test_output_dir / "docker" / "Boundary_net.nc").is_file()
    assert (test_output_dir / "docker" / "Boundary.mdu").is_file()
    assert (test_output_dir / "docker" / "observcrs.ini").is_file()
    assert (test_output_dir / "docker" / "dimr_config.xml").is_file()
