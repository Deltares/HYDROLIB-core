from pathlib import Path

from devtools import debug

from hydrolib.core.basemodel import FileModel
from hydrolib.core.models import DIMR, FMModel

from .utils import test_data_dir, test_output_dir


def test_filemodel_load():
    d = DIMR(filepath="a", model=Path(test_data_dir / "test.mdu"))
    assert isinstance(d.filepath, Path)
    assert isinstance(d.model, FMModel)
    assert isinstance(d.model, FileModel)


def test_filemodel_serialize():
    d = DIMR(filepath="a", model=Path(test_data_dir / "test.mdu"))
    d.save(folder=test_output_dir / "tmp")


def test_tutorial():
    model = FMModel(name="testproject")
    model.save(folder=test_output_dir / "test")
