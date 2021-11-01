from devtools import debug

from hydrolib.core.io.dimr.models import DIMR, FMComponent
from hydrolib.core.io.mdu.models import FMModel
from hydrolib.core.io.net.models import NetworkModel
from hydrolib.core.io.structure.models import FlowDirection, StructureModel, Weir

from ..utils import test_output_dir


def test_from_scratch_docker():
    # TODO Make this model run in Docker to test actual validity
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
