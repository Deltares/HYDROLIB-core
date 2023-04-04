import os

from hydrolib.core.dflowfm.mdu.models import FMModel
from hydrolib.core.utils import working_directory
from hydrolib.tools import prof_to_cross
from tests.utils import (
    assert_files_equal,
    test_input_dir,
    test_output_dir,
    test_reference_dir,
)


def test_prof_to_cross_from_proffiles():
    proflocfile = test_input_dir / "prof_to_cross" / "profloc.xyz"
    profdeffile = test_input_dir / "prof_to_cross" / "profdef.txt"

    crsloc_outfile = test_output_dir / "test_prof_to_cross" / "crsloc.ini"
    crsdef_outfile = test_output_dir / "test_prof_to_cross" / "crsdef.ini"

    crsloc_reffile = test_reference_dir / "prof_to_cross" / "crsloc.ini"
    crsdef_reffile = test_reference_dir / "prof_to_cross" / "crsdef.ini"
    prof_to_cross.prof_to_cross(
        proflocfile, profdeffile, crslocfile=crsloc_outfile, crsdeffile=crsdef_outfile
    )

    assert_files_equal(crsloc_outfile, crsloc_reffile, [0])
    assert_files_equal(crsdef_outfile, crsdef_reffile, [0])


def test_prof_to_cross_from_mdu():
    mdu_infile = test_input_dir / "prof_to_cross" / "tree1d2d.mdu"

    crsloc_outfile = test_output_dir / "test_prof_to_cross" / "crsloc_withxyz.ini"
    crsdef_outfile = test_output_dir / "test_prof_to_cross" / "crsdef_withxyz.ini"

    crsloc_reffile = test_reference_dir / "prof_to_cross" / "crsloc_withxyz.ini"
    crsdef_reffile = test_reference_dir / "prof_to_cross" / "crsdef_withxyz.ini"

    with working_directory(mdu_infile.parent):
        prof_to_cross.prof_to_cross_from_mdu(
            mdu_infile, crslocfile=crsloc_outfile, crsdeffile=crsdef_outfile
        )

    assert_files_equal(crsloc_outfile, crsloc_reffile, [0])
    assert_files_equal(crsdef_outfile, crsdef_reffile, [0])
