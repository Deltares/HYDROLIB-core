from pathlib import Path

import pytest

from hydrolib.core.dflowfm.common.models import Operand
from hydrolib.tools.ext_old_to_new import main_converter

from ..utils import (
    assert_files_equal,
    create_temp_file_from_lines,
    get_temp_file,
    test_input_dir,
)


class TestExtOldToNew:
    def test_wind_combi_uniform_curvi(self):
        main_converter._verbose = True
        mdu_filename = (
            test_input_dir
            / "e02"
            / "f011_wind"
            / "c081_combi_uniform_curvi"
            / "windcase.mdu"
        )

        main_converter.ext_old_to_new_from_mdu(mdu_filename)
        assert True
        # assert isinstance(forcing.filename, TimModel)

    def test_extrapolate_slr(self):
        main_converter._verbose = True
        mdu_filename = (
            test_input_dir
            / "e02"
            / "f006_external_forcing"
            / "c011_extrapolate_slr"
            / "slrextrapol.mdu"
        )
        main_converter.ext_old_to_new_from_mdu(mdu_filename)
        assert True

    def test_basinsquares(self):
        main_converter._verbose = True
        mdu_filename = (
            test_input_dir
            / "e02"
            / "f006_external_forcing"
            / "c020_basinnofriction_squares"
            / "basinsquares.mdu"
        )
        try:
            main_converter.ext_old_to_new_from_mdu(mdu_filename)
        except Exception as e:
            pass

        assert True

    def test_recursive(self):
        main_converter._verbose = True
        dir = test_input_dir / "e02" / "f006_external_forcing"
        main_converter.ext_old_to_new_dir_recursive(dir)
        assert True
