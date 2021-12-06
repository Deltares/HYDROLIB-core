from pathlib import Path
from typing import List, Optional

import pytest
from pydantic import ValidationError

from hydrolib.core.io.bc.models import ForcingModel
from hydrolib.core.io.ini.models import INIBasedModel
from hydrolib.core.io.mdu.models import FMModel

from ..utils import test_input_dir


class TestModels:
    """Test class to test all classes and methods contained in the
    hydrolib.core.io.mdu.models.py module"""

    def test_mdu_file_with_network_is_read_correctly(self):
        input_mdu = (
            test_input_dir
            / "e02"
            / "c11_korte-woerden-1d"
            / "dimr_model"
            / "dflowfm"
            / "FlowFM.mdu"
        )
        fm_model = FMModel(input_mdu)

        assert fm_model.geometry.netfile is not None

        mesh = fm_model.geometry.netfile._mesh1d
        assert len(mesh.branches) > 0
