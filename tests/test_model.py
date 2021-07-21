from pathlib import Path

import pytest

from hydrolib.core.basemodel import FileModel
from hydrolib.core.models import DIMR, FMModel, XYZ

from .utils import test_data_dir, test_output_dir


def test_filemodel_load():
    # If we give a non existing path, it will throw a warning
    with pytest.warns(UserWarning):
        d = DIMR(filepath="a", model=Path(test_data_dir / "test.mdu"))
    assert isinstance(d.filepath, Path)
    assert isinstance(d.model, FMModel)
    assert isinstance(d.model, FileModel)


def test_filemodel_serialize():
    d = DIMR(filepath=f"{test_output_dir}/a", model=Path(test_data_dir / "test.mdu"))
    d.save(folder=test_output_dir / "tmp")
    assert d.filepath.is_file()
    assert d.model.filepath.is_file()
    assert d.model.network.filepath.is_file()


def test_dimr_model():
    test_file = (
        test_data_dir
        / "input"
        / "e02"
        / "c11_korte-woerden-1d"
        / "dimr_model"
        / "dimr_config.xml"
    )
    d = DIMR(filepath=test_file)
    d.save(folder=test_output_dir / "tmp")
    assert d.filepath.is_file()
    assert d.component[1].model.filepath.is_file()


def test_tutorial():
    model = FMModel(name="testproject")
    model.save(folder=test_output_dir / "test")
    assert model.filepath.is_file()
    assert model.network.filepath.is_file()


def test_xyz_model():
    model = XYZ(filepath=Path(test_data_dir / "input/test.xyz"))
    assert len(model.points) == 7, model
    model.filepath = Path(test_output_dir / "test.xyz")
    assert not model.filepath.is_file()
    model.save()
    assert model.filepath.is_file()
