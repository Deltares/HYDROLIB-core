from pathlib import Path

import pytest

from hydrolib.core.dflowfm.common.models import Operand
from hydrolib.tools import extold_to_new

from ..utils import (
    assert_files_equal,
    create_temp_file_from_lines,
    get_temp_file,
    test_input_dir,
)


class TestExtOldToNew:
    def test_wind_combi_uniform_curvi(self):
        extold_to_new._verbose = True
        mdu_filename = (
            test_input_dir
            / "e02"
            / "f011_wind"
            / "c081_combi_uniform_curvi"
            / "windcase.mdu"
        )

        extold_to_new.extold_to_new_from_mdu(mdu_filename)
        assert False

        # assert isinstance(forcing.filename, TimModel)
