from pathlib import Path

import pytest

from hydrolib.core.dflowfm.ext.models import ExtModel
from hydrolib.core.dflowfm.inifield.models import IniFieldModel
from hydrolib.core.dflowfm.structure.models import StructureModel
from hydrolib.tools.ext_old_to_new.utils import construct_filemodel_new_or_existing


@pytest.mark.parametrize("model", [ExtModel, IniFieldModel, StructureModel])
def test_construct_filemodel_new(model):
    file = Path("tests/data/new-file")
    ext_model = construct_filemodel_new_or_existing(model, file)
    assert isinstance(ext_model, model)
    assert ext_model.filepath == file
