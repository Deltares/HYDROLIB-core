from pathlib import Path

import pytest

from hydrolib.core.dflowfm.common.models import Operand
from hydrolib.tools import ext_old_to_new

from ..utils import (
    assert_files_equal,
    create_temp_file_from_lines,
    get_temp_file,
    test_input_dir,
)


class TestExtOldToNew:
    def test_wind_combi_uniform_curvi(self):
        ext_old_to_new._verbose = True
        mdu_filename = ("d:/checkouts/DSCTestbench/trunk/cases/e02_dflowfm/f006_external_forcing/c011_extrapolate_slr/slrextrapol.mdu")
            # test_input_dir
            # / "e02"
            # / "f011_wind"
            # / "c081_combi_uniform_curvi"
            # / "windcase.mdu"
        #)

        ext_old_to_new.ext_old_to_new_from_mdu(mdu_filename)
        assert True
        # assert isinstance(forcing.filename, TimModel)

    def test_recursive(self):
        ext_old_to_new._verbose = True
        dir = ("d:/cases/f006_external_forcing")
            # test_input_dir
            # / "e02"
            # / "f011_wind"
            # / "c081_combi_uniform_curvi"
            # / "windcase.mdu"
        #)

        ext_old_to_new.ext_old_to_new_dir_recursive(dir)
        assert True
        # assert isinstance(forcing.filename, TimModel)
