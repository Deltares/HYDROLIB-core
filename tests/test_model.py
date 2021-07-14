from pathlib import Path
from hydrolib.core.basemodel import DIMR
from .utils import test_data_dir
from devtools import debug


def test_models():
    d = DIMR(model=Path(test_data_dir / "test.mdu"))
    debug(d)
    0 / 0
